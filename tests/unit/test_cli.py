from pathlib import Path

import yaml
from typer.testing import CliRunner

from specguard.cli.main import app

runner = CliRunner()


def _config(tmp_path: Path, provider: str = "speckit") -> Path:
    path = tmp_path / "specguard.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "artifacts": {"provider": provider, "subject": "demo"},
                "git": {"base": "main"},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_help_and_version_do_not_require_artifact_discovery() -> None:
    assert runner.invoke(app, ["--help"]).exit_code == 0
    assert runner.invoke(app, ["version"]).exit_code == 0


def test_change_is_rejected_for_speckit_before_review(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["review", "--config", str(_config(tmp_path)), "--change", "legacy"],
    )
    assert result.exit_code == 4
    assert "OpenSpec" in result.output


def test_conflicting_change_and_subject_are_rejected(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "review",
            "--config",
            str(_config(tmp_path, "openspec")),
            "--change",
            "one",
            "--subject",
            "two",
        ],
    )
    assert result.exit_code == 4
    assert "冲突" in result.output
