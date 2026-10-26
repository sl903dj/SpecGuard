from pathlib import Path

import pytest

from specguard.artifacts.models import ArtifactProviderConfig
from specguard.artifacts.openspec import OpenSpecProvider
from specguard.artifacts.provider import load_bundle
from specguard.errors import UsageError
from tests.fixtures.materialize import materialize


def _current(repo: Path, capability: str, title: str, body: str) -> None:
    path = repo / "openspec" / "specs" / capability / "spec.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"### Requirement: {title}\n\n{body}\n", encoding="utf-8")


def _delta(repo: Path, change: str, title: str) -> None:
    path = repo / "openspec" / "changes" / change / "specs" / "order" / "spec.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "## ADDED Requirements",
                "",
                f"### Requirement: {title}",
                "",
                "The system applies this delta when the change is selected.",
                "",
                "#### Scenario: Applied",
                "",
                "- WHEN selected",
                "- THEN applied",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_provider_rejects_current_spec_symlink_outside_repository(tmp_path: Path) -> None:
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
    provider = OpenSpecProvider()
    config = ArtifactProviderConfig(provider="openspec", subject_kind="current")
    subject = provider.select(repo, config)
    with pytest.raises(UsageError, match="越出"):
        provider.load(repo, subject, config)


def test_single_change_without_current_specs_is_auto_selected(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    bundle = load_bundle(repo, ArtifactProviderConfig(provider="openspec"))
    assert bundle is not None
    assert bundle.subject.subject_id == "add-order"
    assert bundle.subject.subject_kind == "change"
    assert bundle.tasks_available is True
    assert {item.change_semantics for item in bundle.requirements} == {"added"}


def test_multiple_changes_without_current_specs_still_fail(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "two_changes")
    with pytest.raises(UsageError, match="多个进行中的变更"):
        load_bundle(repo, ArtifactProviderConfig(provider="openspec"))


def test_coexistence_without_a_choice_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _current(repo, "order", "List catalog", "The catalog remains available to shoppers.")
    _delta(repo, "add-order", "Create order")
    _delta(repo, "add-tax", "Add tax")
    with pytest.raises(UsageError, match="--baseline"):
        load_bundle(repo, ArtifactProviderConfig(provider="openspec"))


def test_explicit_current_excludes_change_requirements(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _current(repo, "order", "List catalog", "The catalog remains available to shoppers.")
    _delta(repo, "add-order", "Create order")
    bundle = load_bundle(
        repo,
        ArtifactProviderConfig(provider="openspec", subject_kind="current"),
    )
    assert bundle is not None
    assert bundle.subject.subject_id == "current"
    assert bundle.tasks_available is False
    assert bundle.missing == []
    assert {item.title for item in bundle.requirements} == {"List catalog"}
    assert all(item.change_semantics is None for item in bundle.requirements)


def test_explicit_change_excludes_other_current_requirements(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _current(repo, "billing", "Record payment", "The system records payment after checkout.")
    _delta(repo, "add-order", "Create order")
    bundle = load_bundle(
        repo,
        ArtifactProviderConfig(provider="openspec", subject_kind="change", subject="add-order"),
        "add-order",
    )
    assert bundle is not None
    assert bundle.subject.subject_kind == "change"
    assert {item.title for item in bundle.requirements} == {"Create order"}
    assert all(item.change_semantics == "added" for item in bundle.requirements)
    assert all(item.capability is None for item in bundle.requirements)
