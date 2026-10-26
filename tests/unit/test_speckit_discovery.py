import json
from pathlib import Path

import pytest

from specguard.artifacts.models import ArtifactProviderConfig
from specguard.artifacts.speckit import SpecKitProvider
from specguard.errors import UsageError


def _feature(repo: Path, name: str) -> Path:
    feature = repo / "specs" / name
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text(f"# {name}\n", encoding="utf-8")
    return feature


def test_cli_then_config_then_feature_state_precedence(tmp_path: Path) -> None:
    for name in ("one", "two", "three"):
        _feature(tmp_path, name)
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".specify/feature.json").write_text(
        json.dumps({"feature_directory": "specs/three"}), encoding="utf-8"
    )
    provider = SpecKitProvider()
    config = ArtifactProviderConfig(provider="speckit", subject="two")
    assert provider.select(tmp_path, config, "one").subject_id == "one"
    assert provider.select(tmp_path, config).subject_id == "two"
    state_config = ArtifactProviderConfig(provider="speckit")
    assert provider.select(tmp_path, state_config).subject_id == "three"


def test_sole_directory_without_explicit_selection_or_feature_state_is_rejected(
    tmp_path: Path,
) -> None:
    _feature(tmp_path, "only")
    with pytest.raises(UsageError, match="feature.json"):
        SpecKitProvider().select(tmp_path, ArtifactProviderConfig(provider="speckit"))


def test_selection_rejects_ambiguity_bad_state_missing_spec_and_escape(tmp_path: Path) -> None:
    _feature(tmp_path, "one")
    _feature(tmp_path, "two")
    provider = SpecKitProvider()
    config = ArtifactProviderConfig(provider="speckit")
    with pytest.raises(UsageError, match="feature.json"):
        provider.select(tmp_path, config)
    (tmp_path / ".specify").mkdir()
    state = tmp_path / ".specify/feature.json"
    state.write_text("{bad", encoding="utf-8")
    with pytest.raises(UsageError, match="JSON"):
        provider.select(tmp_path, config)
    state.write_text('{"feature_directory": 3}', encoding="utf-8")
    with pytest.raises(UsageError, match="字符串"):
        provider.select(tmp_path, config)
    missing = provider.select(tmp_path, config, "missing")
    with pytest.raises(UsageError, match="不存在"):
        provider.validate(missing)
    with pytest.raises(UsageError, match="越出"):
        provider.select(tmp_path, config, "../../outside")


def test_selection_stays_inside_configured_root_and_rejects_file_symlink(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    _feature(repository, "inside")
    outside = repository / "other"
    outside.mkdir()
    (outside / "spec.md").write_text("- **FR-001**: 仓库内但位于 specs 根之外。\n", encoding="utf-8")
    provider = SpecKitProvider()
    config = ArtifactProviderConfig(provider="speckit", root="specs")
    with pytest.raises(UsageError, match="越出"):
        provider.select(repository, config, "../other")
    secret = tmp_path / "secret.md"
    secret.write_text("SECRET-OUTSIDE", encoding="utf-8")
    feature = repository / "specs" / "inside"
    linked = feature / "plan.md"
    linked.symlink_to(secret)
    subject = provider.select(repository, config, "inside")
    with pytest.raises(UsageError, match="越出"):
        provider.load(repository, subject, config)
    assert "SECRET-OUTSIDE" not in feature.joinpath("spec.md").read_text(encoding="utf-8")


def test_selection_rejects_symlink_escape(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    (repository / "specs").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "spec.md").write_text("# Outside\n", encoding="utf-8")
    (repository / "specs/escaped").symlink_to(outside, target_is_directory=True)
    with pytest.raises(UsageError, match="越出"):
        SpecKitProvider().select(
            repository,
            ArtifactProviderConfig(provider="speckit"),
            "escaped",
        )
