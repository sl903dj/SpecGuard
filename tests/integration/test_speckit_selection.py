from pathlib import Path

import pytest
import yaml

from specguard.config.loader import load_config
from specguard.errors import UsageError
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize_speckit


def test_invalid_state_fails_before_checks_and_report_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = materialize_speckit(tmp_path, "selection")
    config_path = repo / "specguard.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "artifacts": {"provider": "speckit", "root": "specs"},
                "git": {
                    "base": "HEAD",
                    "target": "HEAD",
                    "fail_on_uncommitted_changes": False,
                },
                "checks": {"tests": {"enabled": True, "command": "./mvnw test"}},
            }
        ),
        encoding="utf-8",
    )
    called = False

    def fail_if_called(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("checks must not run")

    monkeypatch.setattr("specguard.pipeline.run_java_checks", fail_if_called)
    state = repo / ".specify/feature.json"
    before = state.read_bytes()
    with pytest.raises(UsageError, match="JSON"):
        run_review(load_config(config_path), config_path)
    assert called is False
    assert not (repo / ".specguard").exists()
    assert state.read_bytes() == before
