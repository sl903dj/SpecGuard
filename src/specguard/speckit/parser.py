import re
from pathlib import Path

from specguard.models.entities import ArtifactReport, Requirement, Scenario, TaskItem

STORY_RE = re.compile(r"^### User Story\s+\d+\s+-\s+(.+)$", re.M)
PRIORITY_RE = re.compile(r"\s*\(Priority:.*\)\s*$")
SCENARIO_RE = re.compile(r"\*\*Given\*\*\s*(.+?)\s*\*\*When\*\*\s*(.+?)\s*\*\*Then\*\*\s*(.+)")
FR_RE = re.compile(r"\b(FR-\d+)\b")
TASK_RE = re.compile(r"^- \[([ xX])\]\s+(.+)$", re.M)
TASK_ID_RE = re.compile(r"^(T\d+)\b")


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def parse_spec(text: str, source: str) -> list[Requirement]:
    requirements: list[Requirement] = []
    stories = list(STORY_RE.finditer(text))
    for index, match in enumerate(stories):
        title = PRIORITY_RE.sub("", match.group(1)).strip()
        end = stories[index + 1].start() if index + 1 < len(stories) else len(text)
        section = text[match.end() : end]
        scenarios = [
            Scenario(name=item.group(3).strip(), source_line=_line_of(text, match.end() + item.start()))
            for item in SCENARIO_RE.finditer(section)
        ]
        requirements.append(
            Requirement(
                identifier=title,
                title=title,
                change_semantics="added",
                scenarios=scenarios,
                source_file=source,
                source_line=_line_of(text, match.start()),
                body=section.strip(),
            )
        )
    seen: set[str] = set()
    for match in FR_RE.finditer(text):
        identifier = match.group(1)
        if identifier in seen:
            continue
        seen.add(identifier)
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        if line_end < 0:
            line_end = len(text)
        requirements.append(
            Requirement(
                identifier=identifier,
                title=identifier,
                change_semantics="added",
                source_file=source,
                source_line=_line_of(text, match.start()),
                body=text[line_start:line_end].strip(),
            )
        )
    return requirements


def parse_tasks(text: str, source: str) -> list[TaskItem]:
    items: list[TaskItem] = []
    for match in TASK_RE.finditer(text):
        body = match.group(2).strip()
        ident = TASK_ID_RE.match(body)
        items.append(
            TaskItem(
                identifier=ident.group(1) if ident else f"task-{_line_of(text, match.start())}",
                text=body,
                marked_complete=match.group(1) in {"x", "X"},
                source_file=source,
                source_line=_line_of(text, match.start()),
            )
        )
    return items


def load_feature(feature_dir: Path, name: str) -> tuple[ArtifactReport, list[Requirement], list[TaskItem]]:
    found: list[str] = []
    missing: list[str] = []
    requirements: list[Requirement] = []
    tasks: list[TaskItem] = []
    spec_path = feature_dir / "spec.md"
    tasks_path = feature_dir / "tasks.md"
    if spec_path.is_file():
        found.append("spec.md")
        requirements = parse_spec(spec_path.read_text(encoding="utf-8"), str(spec_path))
    else:
        missing.append("spec.md")
    if tasks_path.is_file():
        found.append("tasks.md")
        tasks = parse_tasks(tasks_path.read_text(encoding="utf-8"), str(tasks_path))
    else:
        missing.append("tasks.md")
    return (
        ArtifactReport(
            available=bool(requirements),
            found=found,
            missing=missing,
            selected_change=name,
        ),
        requirements,
        tasks,
    )
