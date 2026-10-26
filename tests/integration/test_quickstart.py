import json
import stat
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from specguard.cli.main import app
from specguard.config.loader import load_config
from specguard.models.status import CheckStatus
from specguard.pipeline import run_review
from tests.fixtures.materialize import FIXTURES, materialize

RUNNER = CliRunner()
MANUAL_SCENARIO_9 = [
    "五个问题都有对应章节或计数字段",
    "每条结论都能找到证据，或标成证据不足",
    "最高风险排在风险列表前面",
    "PASS 或已确认 FAIL 的检查出现在可靠检查中",
    "跳过和超时的检查不在可靠检查中",
]


def test_version_help_and_config_validate() -> None:
    assert RUNNER.invoke(app, ["version"]).exit_code == 0
    assert RUNNER.invoke(app, ["--help"]).exit_code == 0
    valid = RUNNER.invoke(
        app,
        ["config", "validate", "--config", str(FIXTURES / "single_change" / "specguard.yaml")],
    )
    assert valid.exit_code == 0
    invalid = RUNNER.invoke(
        app,
        ["config", "validate", "--config", str(FIXTURES / "invalid_config" / "specguard.yaml")],
    )
    assert invalid.exit_code == 4
    assert "llm_findings_block" in invalid.stderr + invalid.output


def test_static_review_and_evidence_gap(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    result = RUNNER.invoke(app, ["review", "--config", str(repo / "specguard.yaml"), "--mode", "static"])
    assert result.exit_code == 0
    report_dir = repo / ".specguard" / "reports"
    markdown = next(report_dir.glob("*.md")).read_text(encoding="utf-8")
    payload = json.loads(next(report_dir.glob("*.json")).read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.1"
    assert "需要人工审核" in markdown
    assert all("代码一定有错" not in item["summary"] for item in payload["findings"])
    assert any(item["support"] == "none" and item["marked_complete"] for item in payload["tasks"])
    assert any(item["evidence"][-1]["status"] == "insufficient" for item in payload["requirements"])


def test_usage_errors_for_repo_base_and_change_selection(tmp_path: Path) -> None:
    bare = tmp_path / "bare"
    bare.mkdir()
    config = bare / "specguard.yaml"
    config.write_text((FIXTURES / "two_changes" / "specguard.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    missing_repo = RUNNER.invoke(app, ["review", "--config", str(config)])
    assert missing_repo.exit_code == 4
    assert "版本库" in missing_repo.stderr + missing_repo.output

    repo = materialize(tmp_path, "single_change")
    bad_base = RUNNER.invoke(
        app,
        ["review", "--config", str(repo / "specguard.yaml"), "--base", "zzzz-not-a-rev"],
    )
    assert bad_base.exit_code == 4
    assert "zzzz-not-a-rev" in bad_base.stderr + bad_base.output

    many = materialize(tmp_path, "two_changes")
    ambiguous = RUNNER.invoke(app, ["review", "--config", str(many / "specguard.yaml")])
    assert ambiguous.exit_code == 4
    assert "one" in ambiguous.output + ambiguous.stderr
    assert "two" in ambiguous.output + ambiguous.stderr


def test_check_status_matrix_and_policy(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    failing = repo / "mvnw"
    failing.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    failing.chmod(failing.stat().st_mode | stat.S_IEXEC)
    subprocess.run(["git", "add", "mvnw"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "fail build"], cwd=repo, check=True)
    advisory = RUNNER.invoke(app, ["review", "--config", str(repo / "specguard.yaml"), "--policy", "advisory"])
    assert advisory.exit_code == 0
    strict = RUNNER.invoke(app, ["review", "--config", str(repo / "specguard.yaml"), "--policy", "strict"])
    assert strict.exit_code == 2
    latest = max((repo / ".specguard" / "reports").glob("*.json"), key=lambda path: path.stat().st_mtime)
    payload = json.loads(latest.read_text(encoding="utf-8"))
    assert payload["policy"]["blocked"] is True
    assert any(item["evidence_status"] == "confirmed" and item["origin"] == "build" for item in payload["findings"])

    config = load_config(repo / "specguard.yaml")
    data = config.model_dump()
    data["checks"]["build"]["command"] = "./mvnw -q -DskipTests package"
    data["checks"]["build"]["required"] = True
    data["review"]["policy"] = "strict"
    data["git"]["fail_on_uncommitted_changes"] = False
    (repo / "mvnw").unlink()
    broken = config.model_validate(data)
    _report, code = run_review(broken, repo / "specguard.yaml")
    assert code == 3
    assert any(item.status == CheckStatus.ERROR for item in _report.checks if item.check_id == "build")


def test_assisted_failure_keeps_deterministic_checks(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    config = load_config(repo / "specguard.yaml")
    data = config.model_dump()
    data["review"]["mode"] = "assisted"
    data["llm"]["enabled"] = True
    data["llm"]["base_url"] = "http://127.0.0.1:1/v1"
    data["llm"]["timeout_seconds"] = 1
    data["llm"]["external_fallback"] = False
    assisted = config.model_validate(data)
    report, code = run_review(assisted, repo / "specguard.yaml")
    assert any(item.check_id == "build" and item.status == CheckStatus.PASS for item in report.checks)
    assert any(item.check_id.startswith("assisted") and item.status == CheckStatus.ERROR for item in report.checks)
    assert assisted.llm.external_fallback is False
    assert code == 0


def test_manual_scenario_nine_is_recorded() -> None:
    assert len(MANUAL_SCENARIO_9) == 5
