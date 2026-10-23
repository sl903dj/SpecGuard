from pathlib import Path

from typer.testing import CliRunner

from specguard.cli.main import app
from tests.fixtures.materialize import materialize

runner = CliRunner()


def _output(result) -> str:
    return (result.output or "") + (getattr(result, "stderr", None) or "")


def _review(repo: Path, *extra: str):
    return runner.invoke(app, ["review", "--config", str(repo / "specguard.yaml"), *extra])


def test_multiple_features_exit_4_without_a_report(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "speckit_many")
    result = _review(repo)
    assert result.exit_code == 4
    text = _output(result)
    assert "001-a" in text
    assert "002-b" in text
    assert not list((repo / ".specguard").glob("**/*"))


def test_both_sources_require_an_explicit_choice(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "speckit_both")
    result = _review(repo)
    assert result.exit_code == 4
    text = _output(result)
    assert "openspec" in text
    assert "speckit" in text
    assert not list((repo / ".specguard").glob("**/*"))


def test_speckit_source_rejects_change_flag(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "speckit_single")
    config = repo / "specguard.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("source: auto", "source: speckit"), encoding="utf-8")
    subprocess_commit(repo)
    result = _review(repo, "--change", "add-order")
    assert result.exit_code == 4
    assert "speckit" in _output(result)
    assert not list((repo / ".specguard").glob("**/*"))


def test_openspec_source_rejects_feature_flag(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    result = _review(repo, "--feature", "001-sample")
    assert result.exit_code == 4
    assert "openspec" in _output(result)


def test_unknown_feature_exits_4_and_names_it(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "speckit_many")
    result = _review(repo, "--feature", "009-missing")
    assert result.exit_code == 4
    assert "009-missing" in _output(result)
    assert not list((repo / ".specguard").glob("**/*"))


def subprocess_commit(repo: Path) -> None:
    import subprocess

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "select speckit"], cwd=repo, check=True, capture_output=True)
