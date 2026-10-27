import re
from pathlib import Path

from specguard.errors import UsageError
from specguard.models.entities import ArtifactReport, MainRequirement, Requirement, Scenario, TaskItem

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


def _scenarios_from(raw_body: str, text: str, body_offset: int) -> list[Scenario]:
    matches = list(SCEN_RE.finditer(raw_body))
    scenarios: list[Scenario] = []
    for index, item in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_body)
        scenarios.append(
            Scenario(
                name=item.group(1).strip(),
                source_line=_line_of(text, body_offset + item.start()),
                body=raw_body[item.end() : end].strip(),
            )
        )
    return scenarios


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
            raw_body = block[match.end() : body_end]
            body = raw_body.strip()
            absolute = header.end() + match.start()
            body_offset = header.end() + match.end()
            scenarios = _scenarios_from(raw_body, text, body_offset)
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


def parse_main_requirements(text: str, source: str) -> list[MainRequirement]:
    items: list[MainRequirement] = []
    for match in REQ_RE.finditer(text):
        title = match.group(1).strip()
        body_end = len(text)
        next_req = REQ_RE.search(text, match.end())
        if next_req:
            body_end = next_req.start()
        body = text[match.end() : body_end].strip()
        items.append(
            MainRequirement(
                title=title,
                body=body,
                source_file=source,
                source_line=_line_of(text, match.start()),
            )
        )
    return items


DELTA_HEADINGS = {"ADDED Requirements", "MODIFIED Requirements", "REMOVED Requirements"}


def parse_current_requirements(text: str, source: str, capability: str) -> list[Requirement]:
    headers = list(re.finditer(r"^## (.+)$", text, re.M))
    delta_spans: list[tuple[int, int]] = []
    for index, header in enumerate(headers):
        if header.group(1).strip() not in DELTA_HEADINGS:
            continue
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        delta_spans.append((header.end(), end))

    def inside_delta(position: int) -> bool:
        return any(start <= position < end for start, end in delta_spans)

    matches = list(REQ_RE.finditer(text))
    plain = [match for match in matches if not inside_delta(match.start())]
    if matches and not plain:
        raise UsageError(f"{source} 只含增量需求，请使用变更审核")
    requirements: list[Requirement] = []
    seen: set[str] = set()
    for match in plain:
        title = match.group(1).strip()
        next_req = REQ_RE.search(text, match.end())
        body_start = match.end()
        raw_body = text[body_start : next_req.start() if next_req else len(text)]
        body = raw_body.strip()
        if not body:
            raise UsageError(f"{source} 需求正文为空: {title}")
        identifier = f"{capability}:{_slug(title)}"
        if identifier in seen:
            raise UsageError(f"{source} 中存在重复需求: {title}")
        seen.add(identifier)
        requirements.append(
            Requirement(
                identifier=identifier,
                title=title,
                capability=capability,
                change_semantics=None,
                scenarios=_scenarios_from(raw_body, text, body_start),
                source_file=source,
                source_line=_line_of(text, match.start()),
                body=body,
                ambiguous=(not SCEN_RE.search(body)) or ("TBD" in body) or ("待定" in body) or len(body) < 12,
                ambiguity_reason="需求信息不足或含糊，无法可靠核验"
                if (not SCEN_RE.search(body)) or ("TBD" in body) or ("待定" in body) or len(body) < 12
                else None,
            )
        )
    return requirements


def load_current(root: Path) -> tuple[list[str], list[Requirement]]:
    specs = root / "specs"
    found: list[str] = []
    requirements: list[Requirement] = []
    if not specs.is_dir():
        return found, requirements
    for path in sorted(specs.glob("**/spec.md")):
        if not path.is_file():
            continue
        resolved = path.resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError as exc:
            raise UsageError(f"OpenSpec 路径越出仓库范围: {path}") from exc
        try:
            text = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise UsageError(f"{path} 不是合法 UTF-8") from exc
        relative = path.relative_to(root).as_posix()
        found.append(relative)
        requirements.extend(parse_current_requirements(text, str(path), path.parent.name))
    return found, requirements


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
            parsed = parse_requirements(change, spec.read_text(encoding="utf-8"), str(spec))
            for item in parsed:
                item.capability = spec.parent.name
            requirements.extend(parsed)
    else:
        missing.append("specs")
    main_specs: list[str] = []
    main_requirements: list[MainRequirement] = []
    if include_main:
        main_root = root / "specs"
        if main_root.is_dir():
            for path in sorted(main_root.glob("**/spec.md")):
                main_specs.append(str(path))
                main_requirements.extend(parse_main_requirements(path.read_text(encoding="utf-8"), str(path)))
    return (
        ArtifactReport(
            available=True,
            found=found,
            missing=missing,
            selected_change=change,
            main_specs=main_specs,
            main_requirements=main_requirements,
        ),
        requirements,
        tasks,
    )
