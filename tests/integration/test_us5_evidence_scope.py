from pathlib import Path

from typer.testing import CliRunner

from specguard.cli.main import app
from tests.fixtures.materialize import commit_all
from tests.fixtures.review_gaps.materialize import blank_repo, write_config

runner = CliRunner()


def test_target_tree_on_a_change_exits_before_writing_a_report(tmp_path: Path) -> None:
    repo = blank_repo(tmp_path)
    spec = repo / "openspec/changes/add-order/specs/order/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "## ADDED Requirements\n\n### Requirement: Create order\n\n系统必须创建订单并且保留记录。\n",
        encoding="utf-8",
    )
    config_path = write_config(repo)
    commit_all(repo, "change")
    before = list((repo / ".specguard").rglob("*")) if (repo / ".specguard").exists() else []
    result = runner.invoke(
        app,
        [
            "review",
            "--config",
            str(config_path),
            "--change",
            "add-order",
            "--evidence-scope",
            "target-tree",
        ],
    )
    combined = f"{result.output}\n{result.stderr}"
    assert result.exit_code == 4
    assert "完整内容证据范围只适用于当前规范" in combined
    after = list((repo / ".specguard").rglob("*")) if (repo / ".specguard").exists() else []
    assert after == before
