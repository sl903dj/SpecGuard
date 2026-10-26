from pathlib import Path

from specguard.artifacts.models import (
    ArtifactBundle,
    ArtifactProviderConfig,
    ArtifactSubject,
    ContextDocument,
)
from specguard.errors import UsageError
from specguard.openspec.discover import active_changes
from specguard.openspec.parser import load_change, load_current


def _inside(path: Path, repository: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(repository.resolve())
    except ValueError as exc:
        raise UsageError(f"OpenSpec 路径越出仓库范围: {path}") from exc
    return resolved


def _relative(path: Path, repository: Path) -> str:
    try:
        return path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError as exc:
        raise UsageError(f"OpenSpec 路径越出仓库范围: {path}") from exc


def has_current_specs(repository: Path, config: ArtifactProviderConfig) -> bool:
    root = repository / (config.root or "openspec")
    specs = root / "specs"
    return specs.is_dir() and any(path.is_file() for path in specs.glob("**/spec.md"))


class OpenSpecProvider:
    name = "openspec"

    def discover(self, repository: Path, config: ArtifactProviderConfig) -> list[str]:
        root = _inside(repository / (config.root or "openspec"), repository)
        return active_changes(root) if root.is_dir() else []

    def select(
        self,
        repository: Path,
        config: ArtifactProviderConfig,
        cli_subject: str | None = None,
        *,
        baseline: bool = False,
    ) -> ArtifactSubject | None:
        root = _inside(repository / (config.root or "openspec"), repository)
        if not root.is_dir():
            return None
        requested = cli_subject or config.subject
        names = active_changes(root)
        current = has_current_specs(repository, config)
        kind = "current" if baseline else config.subject_kind
        if kind == "current":
            if requested:
                raise UsageError("当前规范不能同时指定变更名")
            if not current:
                raise UsageError("找不到当前规范")
            return ArtifactSubject(
                provider="openspec",
                subject_id="current",
                subject_kind="current",
                directory=_inside(root / "specs", repository),
                selection_source="cli" if baseline else "config",  # type: ignore[arg-type]
            )
        if requested is None and current and names and kind is None:
            raise UsageError("当前规范与进行中的变更同时存在，请使用 --baseline 或 --change")
        if requested is None and current and not names:
            return ArtifactSubject(
                provider="openspec",
                subject_id="current",
                subject_kind="current",
                directory=_inside(root / "specs", repository),
                selection_source="legacy_config",
            )
        if requested is None:
            if len(names) > 1:
                raise UsageError("存在多个进行中的变更，请明确选择: " + ", ".join(names))
            if not names:
                return None
            requested = names[0]
        source = "cli" if cli_subject else ("config" if config.subject else "legacy_config")
        directory = _inside(root / "changes" / requested, repository)
        return ArtifactSubject(
            provider="openspec",
            subject_id=requested,
            subject_kind="change",
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

    def load(
        self,
        repository_or_subject: Path | ArtifactSubject,
        subject_or_config: ArtifactSubject | ArtifactProviderConfig,
        config: ArtifactProviderConfig | None = None,
        *,
        include_main_specs: bool = True,
    ) -> ArtifactBundle:
        if config is None:
            subject = repository_or_subject
            options = subject_or_config
            if not isinstance(subject, ArtifactSubject) or not isinstance(options, ArtifactProviderConfig):
                raise TypeError("load 需要 subject 和 config")
            depth = len(Path(options.root or "openspec").parts)
            index = depth if subject.subject_kind == "current" else depth + 1
            repository = subject.directory.parents[index]
        else:
            repository = Path(repository_or_subject)
            subject = subject_or_config
            options = config
            if not isinstance(subject, ArtifactSubject):
                raise TypeError("load 需要 ArtifactSubject")
        root = _inside(repository / (options.root or "openspec"), repository)
        if subject.subject_kind == "current":
            specs = root / "specs"
            if specs.is_dir():
                for path in specs.glob("**/spec.md"):
                    if path.is_file():
                        _inside(path, repository)
            found, requirements = load_current(root)
            limitations = ["任务完整性不可用"]
            if not requirements:
                limitations.append("基于需求的审核不可用")
            for item in requirements:
                item.source_file = _relative(Path(item.source_file), repository)
            return ArtifactBundle(
                subject=subject,
                found=found,
                missing=[],
                requirements=requirements,
                tasks=[],
                tasks_available=False,
                limitations=limitations,
            )
        report, requirements, tasks = load_change(root, subject.subject_id, include_main_specs)
        for item in [*requirements, *tasks]:
            item.source_file = _relative(Path(item.source_file), repository)
        contexts: list[ContextDocument] = []
        if options.include_context:
            for name, kind in (("proposal.md", "proposal"), ("design.md", "design")):
                path = subject.directory / name
                if path.is_file():
                    contexts.append(
                        ContextDocument(
                            kind=kind,  # type: ignore[arg-type]
                            path=_relative(path, repository),
                            content=path.read_text(encoding="utf-8", errors="replace")[:50_000],
                        )
                    )
            for path in report.main_specs:
                main = Path(path)
                contexts.append(
                    ContextDocument(
                        kind="main_spec",
                        path=_relative(main, repository),
                        content=main.read_text(encoding="utf-8", errors="replace")[:50_000],
                    )
                )
        return ArtifactBundle(
            subject=subject,
            found=report.found,
            missing=report.missing,
            requirements=requirements,
            tasks=tasks,
            context_documents=contexts,
            main_specs=report.main_specs,
            main_requirements=report.main_requirements,
        )
