from pathlib import Path

from specguard.openspec.discover import active_changes, select_change
from specguard.openspec.parser import load_change, parse_requirements, parse_tasks
from specguard.errors import UsageError
import pytest


def test_parser_keeps_semantics_and_task_marks(tmp_path: Path) -> None:
    spec = """
## ADDED Requirements

### Requirement: Create order

The system MUST create an order when asked.

#### Scenario: Happy path

- WHEN asked
- THEN an id exists

## REMOVED Requirements

### Requirement: Legacy fee

This behavior is removed and must not be treated as a new defect by itself.

#### Scenario: Gone

- WHEN legacy
- THEN absent
"""
    requirements = parse_requirements("add-order", spec, "spec.md")
    assert {item.change_semantics for item in requirements} == {"added", "removed"}
    added = next(item for item in requirements if item.change_semantics == "added")
    removed = next(item for item in requirements if item.change_semantics == "removed")
    assert added.scenarios[0].name == "Happy path"
    assert added.source_line == spec.splitlines().index("### Requirement: Create order") + 1
    assert added.scenarios[0].source_line == spec.splitlines().index("#### Scenario: Happy path") + 1
    assert removed.scenarios[0].source_line == spec.splitlines().index("#### Scenario: Gone") + 1
    tasks = parse_tasks("- [x] 1.1 Add endpoint\n- [ ] 1.2 Later\n", "tasks.md")
    assert tasks[0].marked_complete is True
    assert tasks[0].identifier == "1.1"
    assert tasks[1].marked_complete is False


def test_missing_openspec_is_unavailable(tmp_path: Path) -> None:
    assert select_change(None, None, True) is None


def test_multiple_changes_require_selection(tmp_path: Path) -> None:
    root = tmp_path / "openspec"
    for name in ("one", "two"):
        (root / "changes" / name).mkdir(parents=True)
    assert active_changes(root) == ["one", "two"]
    with pytest.raises(UsageError) as exc:
        select_change(root, None, True)
    message = str(exc.value)
    assert "one" in message and "two" in message


def test_load_change_lists_missing_artifacts(tmp_path: Path) -> None:
    change = tmp_path / "changes" / "add-order"
    change.mkdir(parents=True)
    artifacts, _requirements, _tasks = load_change(tmp_path, "add-order", False)
    assert "proposal.md" in artifacts.missing
    assert artifacts.available is True
