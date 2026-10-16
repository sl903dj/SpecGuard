import re
from pathlib import Path

from specguard.models.entities import ArtifactReport, Requirement, Scenario, TaskItem

SECTION = {
    "ADDED Requirements": "added",
    "MODIFIED Requirements": "modified",
    "REMOVED Requirements": "removed",
}
REQ_RE = re.compile(r"^### Requirement:\s*(.+)$", re.M)
TASK_RE = re.compile(r"^- \[([ xX])\]\s*(.+)$", re.M)
SCEN_RE = re.compile(r"^#### Scenario:\s*(.+)$", re.M)
EXPECTED = ("proposal.md", "design.md", "tasks.md")


def _slug(text: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return lowered or "requirement"


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def parse_requirements(change: str, text: str, source: str) -> list[Requirement]:
    requirements: list[Requirement] = []
    headers = list(re.finditer(r"^## (.+)$", text, re.M))
    for index, header in enumerate(headers):
        semantics = SECTION.get(header.group(1).strip())
        if semantics is None:
            continue
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[header.end() : end]
        for match in REQ_RE.finditer(block):
            title = match.group(1).strip()
            body_end = len(block)
            next_req = REQ_RE.search(block, match.end())
            if next_req:
                body_end = next_req.start()
            body = block[match.end() : body_end].strip()
            absolute = header.end() + match.start()
            scenarios = [
                Scenario(name=item.group(1).strip(), source_line=_line_of(text, header.end() + item.start()))
                for item in SCEN_RE.finditer(body)
            ]
            ambiguous = (not scenarios) or ("TBD" in body) or ("待定" in body) or len(body) < 12
            reason = None
            if ambiguous:
                reason = "需求信息不足或含糊，无法可靠核验"
            requirements.append(
                Requirement(
                    identifier=f"{change}:{semantics}:{_slug(title)}",
                    title=title,
                    change_semantics=semantics,  # type: ignore[arg-type]
                    scenarios=scenarios,
                    source_file=source,
                    source_line=_line_of(text, absolute),
                    body=body,
                    ambiguous=ambiguous,
                    ambiguity_reason=reason,
                )
            )
    return requirements


def parse_tasks(text: str, source: str) -> list[TaskItem]:
    items: list[TaskItem] = []
    for match in TASK_RE.finditer(text):
        raw = match.group(2).strip()
        number = re.match(r"^(\d+(?:\.\d+)*)\s+(.*)$", raw)
        if number:
            identifier, title = number.group(1), number.group(2)
        else:
            identifier, title = raw, raw
        items.append(
            TaskItem(
                identifier=identifier,
                text=title,
                marked_complete=match.group(1).lower() == "x",
                source_file=source,
                source_line=_line_of(text, match.start()),
            )
        )
    return items


def load_change(root: Path, change: str, include_main: bool) -> tuple[ArtifactReport, list[Requirement], list[TaskItem]]:
    change_dir = root / "changes" / change
    found: list[str] = []
    missing: list[str] = []
    requirements: list[Requirement] = []
    tasks: list[TaskItem] = []
    if not change_dir.is_dir():
        return (
            ArtifactReport(available=True, found=[], missing=list(EXPECTED) + ["specs"], selected_change=change),
            [],
            [],
        )
    for name in EXPECTED:
        path = change_dir / name
        if path.is_file():
            found.append(name)
            text = path.read_text(encoding="utf-8")
            if name == "tasks.md":
                tasks.extend(parse_tasks(text, str(path)))
        else:
            missing.append(name)
    spec_files = sorted((change_dir / "specs").glob("**/spec.md")) if (change_dir / "specs").is_dir() else []
    if spec_files:
        found.append("specs")
        for spec in spec_files:
            requirements.extend(parse_requirements(change, spec.read_text(encoding="utf-8"), str(spec)))
    else:
        missing.append("specs")
    main_specs: list[str] = []
    if include_main:
        main_root = root / "specs"
        if main_root.is_dir():
            main_specs = [str(path) for path in sorted(main_root.glob("**/spec.md"))]
    return (
        ArtifactReport(
            available=True,
            found=found,
            missing=missing,
            selected_change=change,
            main_specs=main_specs,
        ),
        requirements,
        tasks,
    )
