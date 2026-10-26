from pathlib import Path

from specguard.artifacts.provider import load_bundle
from specguard.config.loader import load_config
from specguard.openspec.parser import load_change
from tests.fixtures.materialize import materialize


def test_openspec_provider_matches_legacy_normalized_artifacts(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    config = load_config(repo / "specguard.yaml")
    legacy_report, legacy_requirements, legacy_tasks = load_change(
        repo / "openspec", "add-order", True
    )
    bundle = load_bundle(
        repo,
        config.artifact_provider_config(),
        include_main_specs=True,
    )
    assert bundle is not None
    assert bundle.found == legacy_report.found
    assert bundle.missing == legacy_report.missing
    assert [
        (item.identifier, item.change_semantics) for item in bundle.requirements
    ] == [
        (item.identifier, item.change_semantics) for item in legacy_requirements
    ]
    assert [
        (item.identifier, item.marked_complete) for item in bundle.tasks
    ] == [
        (item.identifier, item.marked_complete) for item in legacy_tasks
    ]
