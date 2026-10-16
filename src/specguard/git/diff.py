import re
from pathlib import Path

from specguard.git.repository import run_git
from specguard.models.entities import ChangedFile, LineRange

NAME_STATUS = re.compile(r"^([AMDRT])(\d+)?\t(.+)$")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_name_status(text: str, committed: bool) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        code = parts[0]
        kind = code[0]
        if kind == "A" and len(parts) == 2:
            files.append(ChangedFile(path=parts[1], change_type="added", committed=committed))
        elif kind == "M" and len(parts) == 2:
            files.append(ChangedFile(path=parts[1], change_type="modified", committed=committed))
        elif kind == "D" and len(parts) == 2:
            files.append(ChangedFile(path=parts[1], change_type="deleted", committed=committed))
        elif kind == "R" and len(parts) == 3:
            files.append(
                ChangedFile(
                    path=parts[2],
                    previous_path=parts[1],
                    change_type="renamed",
                    committed=committed,
                )
            )
    return files


def attach_ranges(files: list[ChangedFile], diff_text: str) -> None:
    current: ChangedFile | None = None
    by_path = {item.path: item for item in files}
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            current = None
            match = re.search(r" b/(.+)$", line)
            if match:
                current = by_path.get(match.group(1))
            continue
        if current is None or not line.startswith("@@"):
            continue
        hunk = HUNK.match(line)
        if not hunk:
            continue
        start = int(hunk.group(1))
        count = int(hunk.group(2) or "1")
        if start <= 0 or count <= 0:
            continue
        current.line_ranges.append(LineRange(start=start, end=start + count - 1))


def collect_changes(
    repo: Path,
    base: str,
    target: str,
    include_worktree: bool,
) -> list[ChangedFile]:
    status = run_git(
        ["diff", "--name-status", "--find-renames", base, target],
        repo,
    )
    files = parse_name_status(status.stdout, committed=True)
    patch = run_git(["diff", "--find-renames", "-U0", base, target], repo)
    attach_ranges(files, patch.stdout)
    if include_worktree:
        work = run_git(["diff", "--name-status", "HEAD"], repo)
        extra = parse_name_status(work.stdout, committed=False)
        files.extend(extra)
    return files
