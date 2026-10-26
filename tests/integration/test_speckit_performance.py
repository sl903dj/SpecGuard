import time
from pathlib import Path

from specguard.artifacts.models import ArtifactProviderConfig
from specguard.artifacts.speckit import SpecKitProvider


def test_discovery_and_large_feature_parsing_complete_under_five_seconds(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    specs = repo / "specs"
    specs.mkdir(parents=True)
    for index in range(100):
        feature = specs / f"{index:03d}-feature"
        feature.mkdir()
        feature.joinpath("spec.md").write_text(
            "\n".join(
                f"- **FR-{index * 10 + item:04d}**: Requirement {item}"
                for item in range(10)
            ),
            encoding="utf-8",
        )
        feature.joinpath("tasks.md").write_text(
            "\n".join(
                f"- [ ] T{index * 50 + item:05d} Task {item}"
                for item in range(50)
            ),
            encoding="utf-8",
        )
    config = ArtifactProviderConfig(
        provider="speckit",
        root="specs",
        subject="000-feature",
        include_context=False,
    )
    provider = SpecKitProvider()
    started = time.perf_counter()
    assert len(provider.discover(repo, config)) == 100
    for subject_id in provider.discover(repo, config):
        selected = provider.select(
            repo,
            config.model_copy(update={"subject": subject_id}),
        )
        bundle = provider.load(repo, selected, config)
        assert len(bundle.requirements) == 10
        assert len(bundle.tasks) == 50
    assert time.perf_counter() - started < 5
