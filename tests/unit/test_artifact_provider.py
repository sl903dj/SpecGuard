from pathlib import Path

from specguard.artifacts.models import ArtifactProviderConfig
from specguard.artifacts.provider import provider_for


def _write_standard(repo: Path) -> Path:
    feature = repo / "specs/003-demo"
    feature.mkdir(parents=True)
    (repo / ".specify").mkdir()
    (feature / "spec.md").write_text(
        "# Feature\n\n- **FR-001**: 系统必须工作。\n", encoding="utf-8"
    )
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (feature / "tasks.md").write_text("- [X] T001 [P] [US1] 实现功能\n", encoding="utf-8")
    (feature / "research.md").write_text("# Research\n", encoding="utf-8")
    return feature


def test_speckit_provider_loads_core_and_context_without_writes(tmp_path: Path) -> None:
    feature = _write_standard(tmp_path)
    before = {p: p.read_bytes() for p in feature.rglob("*") if p.is_file()}
    provider = provider_for("speckit")
    config = ArtifactProviderConfig(provider="speckit", subject="003-demo")
    subject = provider.select(tmp_path, config, None)
    provider.validate(tmp_path, subject)
    bundle = provider.load(tmp_path, subject, config)
    assert bundle.found == ["spec.md", "plan.md", "tasks.md"]
    assert {item.kind for item in bundle.context_documents} >= {"plan", "research"}
    assert bundle.requirements[0].evidence == []
    assert before == {p: p.read_bytes() for p in feature.rglob("*") if p.is_file()}


def test_registry_exposes_both_read_only_providers() -> None:
    assert provider_for("openspec").name == "openspec"
    assert provider_for("speckit").name == "speckit"
