from pathlib import Path

import pytest

from specguard.errors import UsageError
from specguard.openspec.parser import load_current, parse_current_requirements


def test_current_requirement_keeps_capability_and_has_no_delta_semantics() -> None:
    text = """
### Requirement: Create order

The system creates an order for the shopper.

#### Scenario: Happy path

- WHEN asked
- THEN an id exists
"""
    requirements = parse_current_requirements(text, "specs/order/spec.md", "order")
    assert len(requirements) == 1
    item = requirements[0]
    assert item.identifier == "order:create-order"
    assert item.change_semantics is None
    assert item.capability == "order"
    assert item.source_line == 2
    assert item.scenarios[0].name == "Happy path"
    assert item.scenarios[0].source_line == 6


def test_duplicate_title_fails_before_checks() -> None:
    text = """
### Requirement: Create order

The system creates an order for the shopper.

### Requirement: Create order

The system creates another order for the shopper.
"""
    with pytest.raises(UsageError, match="重复需求"):
        parse_current_requirements(text, "specs/order/spec.md", "order")


def test_empty_body_fails_before_checks() -> None:
    text = """
### Requirement: Empty

### Requirement: Create order

The system creates an order for the shopper.
"""
    with pytest.raises(UsageError, match="需求正文为空"):
        parse_current_requirements(text, "specs/order/spec.md", "order")


def test_delta_only_file_is_rejected() -> None:
    text = """
## ADDED Requirements

### Requirement: Create order

The system creates an order for the shopper.
"""
    with pytest.raises(UsageError, match="请使用变更审核"):
        parse_current_requirements(text, "specs/order/spec.md", "order")


def test_symlink_outside_repository_fails_before_checks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "spec.md").write_text(
        "### Requirement: Escaped\n\nThis body lives outside the repository.\n",
        encoding="utf-8",
    )
    spec = repo / "openspec" / "specs" / "order" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.symlink_to(outside / "spec.md")
    with pytest.raises(UsageError, match="越出"):
        load_current(repo / "openspec")


def test_invalid_utf8_fails_before_checks(tmp_path: Path) -> None:
    path = tmp_path / "specs" / "order" / "spec.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"### Requirement: Broken\n\n\xff\n")
    with pytest.raises(UsageError, match="UTF-8"):
        load_current(tmp_path)
