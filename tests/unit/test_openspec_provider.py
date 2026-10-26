from pathlib import Path

import pytest

from specguard.artifacts.models import ArtifactProviderConfig
from specguard.artifacts.openspec import OpenSpecProvider
from specguard.errors import UsageError


def _change(repo: Path, name: str) -> None:
    change = repo / "openspec/changes" / name
    (change / "specs/order").mkdir(parents=True)
    (change / "proposal.md").write_text("# Proposal\n", encoding="utf-8")
    (change / "design.md").write_text("# Design\n", encoding="utf-8")
    (change / "tasks.md").write_text("- [x] 1.1 Build\n", encoding="utf-8")
    (change / "specs/order/spec.md").write_text(
        "## ADDED Requirements\n\n### Requirement: Create order\n\n"
        "The system MUST create an order.\n\n#### Scenario: Happy\n\n- WHEN requested\n- THEN created\n",
        encoding="utf-8",
    )


def test_openspec_adapter_preserves_delta_semantics_and_tasks(tmp_path: Path) -> None:
    _change(tmp_path, "one")
    provider = OpenSpecProvider()
    config = ArtifactProviderConfig(provider="openspec", subject="one")
    subject = provider.select(tmp_path, config)
    assert subject is not None
    bundle = provider.load(tmp_path, subject, config)
    assert bundle.requirements[0].change_semantics == "added"
    assert bundle.tasks[0].marked_complete is True
    assert bundle.missing == []


def test_openspec_multiple_changes_require_selection(tmp_path: Path) -> None:
    _change(tmp_path, "one")
    _change(tmp_path, "two")
    with pytest.raises(UsageError, match="明确选择"):
        OpenSpecProvider().select(tmp_path, ArtifactProviderConfig(provider="openspec"))
