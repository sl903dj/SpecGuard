import json
import re
from pathlib import Path

from specguard.artifacts.models import (
    ArtifactBundle,
    ArtifactProviderConfig,
    ArtifactSubject,
    ContextDocument,
)
from specguard.errors import UsageError
from specguard.models.entities import Requirement, Scenario, TaskItem, UserStory

REQUIREMENT_RE = re.compile(r"^\s*(?:[-*]\s*)?\*\*(FR-\d+)\*\*\s*:\s*(.+?)\s*$", re.I)
TASK_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(T\d+)\b(.*)$", re.I)
STORY_RE = re.compile(
    r"^#{2,4}\s+User Story\s+(\d+).*?\(Priority:\s*(P\d+)\)", re.I
)
SCENARIO_RE = re.compile(
    r"^\s*\d+\.\s+.*?\*\*Given\*\*.+?\*\*When\*\*.+?\*\*Then\*\*.+$", re.I
)
PLACEHOLDER_RE = re.compile(
    r"\[(?:FEATURE NAME|FEATURE|CHECKLIST TYPE|Brief Title|DATE|STATUS|link|###-feature-name)\]"
    r"|NEEDS CLARIFICATION|\$ARGUMENTS|\{\{[^}\n]+\}\}",
    re.I,
)
MISSING_ID_RE = re.compile(
    r"^\s*(?:###\s+Requirement\s*:|[-*]\s+\*\*(?!FR-\d+\*\*).+\*\*\s*:|[-*]\s+(?:系统必须|System MUST)\b)",
    re.I,
)
CORE = ("spec.md", "plan.md", "tasks.md")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError(f"{path} 不是合法 UTF-8") from exc


def _read_inside(path: Path, boundary: Path) -> str:
    _ensure_inside(path, boundary, "工件文件")
    return _read(path)


def _relative(path: Path, repository: Path) -> str:
    try:
        return path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError as exc:
        raise UsageError(f"工件路径越出仓库范围: {path}") from exc


def _ensure_inside(path: Path, parent: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(parent.resolve())
    except ValueError as exc:
        raise UsageError(f"{label}越出仓库范围: {path}") from exc
    return resolved


def _reject_placeholders(text: str, source: str) -> None:
    match = PLACEHOLDER_RE.search(text)
    if match:
        raise UsageError(f"{source} 含未替换的关键模板占位符: {match.group(0)}")


def parse_spec_document(text: str, source: str) -> tuple[list[Requirement], list[UserStory]]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    _reject_placeholders(text, source)
    lines = text.splitlines()
    stories: list[UserStory] = []
    active: UserStory | None = None
    story_scenarios: list[Scenario] = []
    requirements: list[Requirement] = []
    seen: set[str] = set()

    for number, line in enumerate(lines, 1):
        heading = STORY_RE.match(line)
        if heading:
            active = UserStory(
                identifier=f"US{heading.group(1)}",
                title=line.strip(),
                priority=heading.group(2).upper(),
                source_line=number,
            )
            stories.append(active)
            story_scenarios = []
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= 3:
                active = None
                story_scenarios = []
            continue
        if SCENARIO_RE.match(line):
            scenario = Scenario(name=line.strip(), source_line=number)
            story_scenarios.append(scenario)
            if active is not None:
                active.scenarios.append(scenario)
            continue
        match = REQUIREMENT_RE.match(line)
        if not match:
            if MISSING_ID_RE.match(line):
                raise UsageError(f"{source}:{number} 含缺少稳定需求 ID 的需求条目")
            continue
        identifier = match.group(1).upper()
        if identifier in seen:
            raise UsageError(f"{source} 中存在重复需求 ID: {identifier}")
        seen.add(identifier)
        body = match.group(2).strip()
        mentions = {item.upper() for item in re.findall(r"\bUS\d+\b", body, re.I)}
        known = {item.identifier for item in stories}
        user_story_id = active.identifier if active is not None else None
        if user_story_id is None and len(mentions) == 1 and mentions <= known:
            user_story_id = next(iter(mentions))
        requirements.append(
            Requirement(
                identifier=identifier,
                title=body.rstrip("。."),
                body=body,
                change_semantics=None,
                user_story_id=user_story_id,
                priority=active.priority if active is not None else None,
                scenarios=list(story_scenarios) if active is not None else [],
                source_file=source,
                source_line=number,
                ambiguous=not body,
                ambiguity_reason="需求正文为空" if not body else None,
            )
        )
    return requirements, stories


def parse_requirements(text: str, source: str) -> list[Requirement]:
    return parse_spec_document(text, source)[0]


def parse_tasks(text: str, source: str) -> list[TaskItem]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    _reject_placeholders(text, source)
    tasks: list[TaskItem] = []
    seen: set[str] = set()
    for number, line in enumerate(text.splitlines(), 1):
        match = TASK_RE.match(line)
        if not match:
            continue
        identifier = match.group(2).upper()
        if identifier in seen:
            raise UsageError(f"{source} 中存在重复任务 ID: {identifier}")
        seen.add(identifier)
        rest = match.group(3).strip()
        parallel = bool(re.search(r"(?:^|\s)\[P\](?:\s|$)", rest, re.I))
        story_match = re.search(r"(?:^|\s)\[(US\d+)\](?:\s|$)", rest, re.I)
        story = story_match.group(1).upper() if story_match else None
        text_body = re.sub(r"(?:^|\s)\[(?:P|US\d+)\](?=\s|$)", " ", rest, flags=re.I)
        tasks.append(
            TaskItem(
                identifier=identifier,
                text=" ".join(text_body.split()),
                marked_complete=match.group(1).lower() == "x",
                parallel=parallel,
                user_story_id=story,
                source_file=source,
                source_line=number,
            )
        )
    return tasks


class SpecKitProvider:
    name = "speckit"

    def discover(self, repository: Path, config: ArtifactProviderConfig) -> list[str]:
        root = _ensure_inside(repository / (config.root or "specs"), repository, "Spec Kit 根目录")
        if not root.is_dir():
            return []
        return sorted(path.name for path in root.iterdir() if path.is_dir())

    def select(
        self,
        repository: Path,
        config: ArtifactProviderConfig,
        cli_subject: str | None = None,
    ) -> ArtifactSubject:
        repository = repository.resolve()
        root = _ensure_inside(repository / (config.root or "specs"), repository, "Spec Kit 根目录")
        requested = cli_subject or config.subject
        source = "cli" if cli_subject else "config"
        if requested is None:
            state = repository / ".specify/feature.json"
            if state.exists():
                _ensure_inside(state, repository, "Spec Kit 状态文件")
                try:
                    payload = json.loads(_read(state))
                except (OSError, json.JSONDecodeError) as exc:
                    raise UsageError(f".specify/feature.json 不是合法 JSON: {exc}") from exc
                requested = payload.get("feature_directory") if isinstance(payload, dict) else None
                if not isinstance(requested, str) or not requested.strip():
                    raise UsageError(".specify/feature.json 的 feature_directory 必须是非空字符串")
                source = "feature_state"
            else:
                candidates = self.discover(repository, config)
                detail = f": {', '.join(candidates)}" if candidates else ""
                raise UsageError(
                    "无法选择 Spec Kit 功能：请使用 --subject、配置 artifacts.subject，"
                    f"或提供有效的 .specify/feature.json{detail}"
                )
        candidate = Path(requested)
        if not candidate.is_absolute():
            root_parts = Path(config.root or "specs").parts
            candidate = repository / candidate if candidate.parts[: len(root_parts)] == root_parts else root / candidate
        directory = _ensure_inside(candidate, root, "Spec Kit 功能目录")
        return ArtifactSubject(
            provider="speckit",
            subject_id=directory.name,
            directory=directory,
            selection_source=source,  # type: ignore[arg-type]
        )

    def validate(
        self,
        repository_or_subject: Path | ArtifactSubject,
        subject: ArtifactSubject | None = None,
    ) -> None:
        selected = subject or repository_or_subject
        if not isinstance(selected, ArtifactSubject):
            raise TypeError("缺少 ArtifactSubject")
        if not selected.directory.is_dir():
            raise UsageError(f"Spec Kit 功能目录不存在: {selected.directory}")
        spec = selected.directory / "spec.md"
        if not spec.is_file():
            raise UsageError(f"Spec Kit 功能目录缺少 spec.md: {selected.directory}")
        _ensure_inside(spec, selected.directory, "spec.md")

    def load(
        self,
        repository_or_subject: Path | ArtifactSubject,
        subject_or_config: ArtifactSubject | ArtifactProviderConfig,
        config: ArtifactProviderConfig | None = None,
    ) -> ArtifactBundle:
        if config is None:
            subject = repository_or_subject
            options = subject_or_config
            if not isinstance(subject, ArtifactSubject) or not isinstance(options, ArtifactProviderConfig):
                raise TypeError("load 需要 subject 和 config")
            repository = _infer_repository(subject, options)
        else:
            repository = Path(repository_or_subject)
            subject = subject_or_config
            options = config
            if not isinstance(subject, ArtifactSubject):
                raise TypeError("load 需要 ArtifactSubject")
        self.validate(subject)
        found = [name for name in CORE if (subject.directory / name).is_file()]
        missing = [name for name in CORE if name not in found]
        spec = subject.directory / "spec.md"
        requirements, stories = parse_spec_document(_read_inside(spec, subject.directory), _relative(spec, repository))
        tasks_path = subject.directory / "tasks.md"
        tasks = (
            parse_tasks(_read_inside(tasks_path, subject.directory), _relative(tasks_path, repository))
            if tasks_path.is_file()
            else []
        )
        context = self._contexts(repository, subject.directory) if options.include_context else []
        limitations = [f"缺少 Spec Kit 工件: {name}" for name in missing]
        return ArtifactBundle(
            subject=subject,
            found=found,
            missing=missing,
            requirements=requirements,
            user_stories=stories,
            tasks=tasks,
            context_documents=context,
            limitations=limitations,
        )

    def _contexts(self, repository: Path, feature: Path) -> list[ContextDocument]:
        fixed = {
            "plan.md": "plan",
            "research.md": "research",
            "data-model.md": "data_model",
            "quickstart.md": "quickstart",
        }
        paths: list[tuple[Path, str]] = [
            (feature / name, kind) for name, kind in fixed.items() if (feature / name).is_file()
        ]
        for directory, kind in (("contracts", "contract"), ("checklists", "checklist")):
            root = feature / directory
            if root.is_dir():
                paths.extend((path, kind) for path in sorted(root.rglob("*")) if path.is_file())
        documents: list[ContextDocument] = []
        for path, kind in paths:
            content = _read_inside(path, feature)
            title_match = re.search(r"^#\s+(.+)$", content, re.M)
            documents.append(
                ContextDocument(
                    kind=kind,  # type: ignore[arg-type]
                    path=_relative(path, repository),
                    title=title_match.group(1).strip() if title_match else None,
                    content=content[:50_000],
                )
            )
        return documents


def _infer_repository(subject: ArtifactSubject, config: ArtifactProviderConfig) -> Path:
    repository = subject.directory.parent
    for _part in Path(config.root or "specs").parts:
        repository = repository.parent
    return repository
