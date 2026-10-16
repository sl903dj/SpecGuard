from pathlib import Path

from specguard.errors import UsageError


def find_openspec_root(repo: Path, configured: str) -> Path | None:
    candidate = (repo / configured).resolve()
    if candidate.is_dir():
        return candidate
    return None


def active_changes(root: Path) -> list[str]:
    changes = root / "changes"
    if not changes.is_dir():
        return []
    return sorted(
        path.name
        for path in changes.iterdir()
        if path.is_dir() and path.name != "archive"
    )


def select_change(root: Path | None, requested: str | None, require_selection: bool) -> str | None:
    if root is None:
        return None
    names = active_changes(root)
    if requested:
        return requested
    if len(names) > 1 and require_selection:
        raise UsageError("存在多个进行中的变更，请明确选择: " + ", ".join(names))
    if len(names) == 1:
        return names[0]
    return None
