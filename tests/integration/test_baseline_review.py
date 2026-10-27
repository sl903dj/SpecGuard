import json
import subprocess
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specguard.cli.main import app
from specguard.config.loader import load_config
from specguard.errors import UsageError
from specguard.pipeline import run_review
from tests.fixtures.materialize import commit_all, git, init_repo, materialize_baseline

runner = CliRunner()


def _openspec_bytes(repo: Path) -> dict[str, bytes]:
    root = repo / "openspec"
    return {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_current_only_review_uses_only_in_range_evidence(tmp_path: Path) -> None:
    repo = materialize_baseline(tmp_path)
    git(repo, "checkout", "-b", "review")
    java = repo / "src/main/java/com/example/Order.java"
    java.parent.mkdir(parents=True, exist_ok=True)
    java.write_text("public class Order {}\n", encoding="utf-8")
    commit_all(repo, "add order code")
    before = _openspec_bytes(repo)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    config = load_config(repo / "specguard.yaml")
    report, code = run_review(config, repo / "specguard.yaml")
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    payload = json.loads(Path(report.metadata.output_paths[1]).read_text(encoding="utf-8"))
    by_id = {item["identifier"]: item for item in payload["requirements"]}
    assert code == 0
    assert set(by_id) == {"order:create-order", "order:ship-notice", "billing:record-payment"}
    assert all(item["change_semantics"] is None for item in payload["requirements"])
    assert by_id["order:create-order"]["evidence"][0]["status"] == "inferred"
    assert by_id["order:create-order"]["evidence"][0]["file"].endswith("Order.java")
    assert by_id["order:ship-notice"]["evidence"][0]["status"] == "insufficient"
    assert by_id["billing:record-payment"]["evidence"][0]["status"] == "insufficient"
    cited = {
        evidence.get("file")
        for item in payload["requirements"]
        for evidence in item["evidence"]
        if evidence.get("file")
    }
    assert not any(path and path.endswith("Outside.java") for path in cited)
    assert {item["path"] for item in payload["changed_files"]} == {
        "src/main/java/com/example/Order.java"
    }
    assert payload["schema_version"] == "1.3"
    assert payload["metadata"]["subject_kind"] == "current"
    assert payload["metadata"]["subject_id"] == "current"
    assert payload["metadata"]["tasks_available"] is False
    assert payload["metadata"]["change"] is None
    assert payload["artifacts"]["selected_change"] is None
    assert payload["artifacts"]["missing"] == []
    assert "当前规范" in text
    assert "任务完整性不可用" in text
    assert "任务完整性缺口" not in text
    assert _openspec_bytes(repo) == before
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == head
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
    assert status.strip()
    assert all(".specguard" in line for line in status.splitlines())


def _coexistence_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "both"
    repo.mkdir()
    current = repo / "openspec" / "specs" / "catalog" / "spec.md"
    current.parent.mkdir(parents=True)
    current.write_text(
        "### Requirement: List catalog\n\nThe catalog remains available to shoppers.\n",
        encoding="utf-8",
    )
    change = repo / "openspec" / "changes" / "add-order" / "specs" / "order" / "spec.md"
    change.parent.mkdir(parents=True)
    change.write_text(
        "\n".join(
            [
                "## ADDED Requirements",
                "",
                "### Requirement: Create order",
                "",
                "The system MUST create an order when the caller submits items.",
                "",
                "#### Scenario: Happy path",
                "",
                "- WHEN the caller submits items",
                "- THEN an order id is returned",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (repo / "openspec" / "changes" / "add-tax").mkdir(parents=True)
    (repo / "specguard.yaml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "artifacts": {"provider": "openspec", "root": "openspec"},
                "git": {"base": "main", "target": "HEAD"},
                "review": {"mode": "static", "policy": "advisory"},
                "checks": {"build": {"enabled": False}, "tests": {"enabled": False}},
                "llm": {"enabled": False, "external_fallback": False},
                "security": {"isolate_builds": False},
            }
        ),
        encoding="utf-8",
    )
    init_repo(repo)
    commit_all(repo, "base")
    return repo


def test_coexistence_requires_a_choice_before_any_report(tmp_path: Path) -> None:
    repo = _coexistence_repo(tmp_path)
    config = load_config(repo / "specguard.yaml")
    with pytest.raises(UsageError, match="--baseline"):
        run_review(config, repo / "specguard.yaml")
    assert not (repo / ".specguard").exists()

    current, _code = run_review(config, repo / "specguard.yaml", baseline=True)
    assert current.metadata.subject_kind == "current"
    assert current.metadata.change is None
    assert {item.title for item in current.requirements} == {"List catalog"}

    selected, _code = run_review(config, repo / "specguard.yaml", cli_subject="add-order")
    assert selected.metadata.subject_kind == "change"
    assert selected.metadata.change == "add-order"
    assert {item.title for item in selected.requirements} == {"Create order"}
    assert {item.change_semantics for item in selected.requirements} == {"added"}


def test_broken_current_spec_stops_before_a_report(tmp_path: Path) -> None:
    repo = materialize_baseline(tmp_path)
    spec = repo / "openspec" / "specs" / "order" / "spec.md"
    spec.write_text("### Requirement: Empty\n\n", encoding="utf-8")
    commit_all(repo, "break spec")
    before = spec.read_bytes()
    config = load_config(repo / "specguard.yaml")
    with pytest.raises(UsageError, match="需求正文为空"):
        run_review(config, repo / "specguard.yaml")
    assert not (repo / ".specguard").exists()
    assert spec.read_bytes() == before


def test_empty_revision_range_stays_insufficient_and_explains(tmp_path: Path) -> None:
    repo = materialize_baseline(tmp_path)
    config = load_config(repo / "specguard.yaml")
    report, code = run_review(config, repo / "specguard.yaml")
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    assert code == 0
    assert report.changed_files == []
    assert report.requirements
    assert all(item.evidence[-1].status == "insufficient" for item in report.requirements)
    assert "选定版本范围内没有可核验证据" in text
    assert "选定版本范围内没有可核验证据" in report.metadata.limitations


def test_cli_baseline_reviews_current_only_repository(tmp_path: Path) -> None:
    repo = materialize_baseline(tmp_path)
    result = runner.invoke(app, ["review", "--config", str(repo / "specguard.yaml"), "--baseline"])
    assert result.exit_code == 0, result.output
    payload = json.loads(next(Path(repo).rglob("*.json")).read_text(encoding="utf-8"))
    assert payload["metadata"]["subject_kind"] == "current"
    assert payload["metadata"]["change"] is None
