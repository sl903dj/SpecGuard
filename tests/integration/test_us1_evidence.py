from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import commit_all, git
from tests.fixtures.review_gaps.materialize import blank_repo, write_config


def test_evidence_cases_do_not_rewrite_requirements_or_history(tmp_path: Path) -> None:
    repo = blank_repo(tmp_path)
    git(repo, "checkout", "-b", "review")
    spec = repo / "openspec/changes/add-order/specs/order/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "\n".join(
            [
                "## ADDED Requirements",
                "",
                "### Requirement: Create order",
                "",
                "系统必须创建订单。",
                "",
                "#### Scenario: Happy path",
                "",
                "- THEN an order id is returned",
                "",
                "#### Scenario: Empty assert",
                "",
                "- THEN nothing useful happens here",
                "",
                "### Requirement: Save Order.java",
                "",
                "系统必须保存 Order.java。",
                "",
                "### Requirement: Quiet rule",
                "",
                "系统必须保持安静并且不引用文件名。",
                "",
                "### Requirement: Bare rule",
                "",
                "系统必须存在一条没有场景的要求。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    java = repo / "src/main/java/Order.java"
    java.parent.mkdir(parents=True)
    java.write_text("class Order { String id = \"add-order:added:create-order\"; }\n", encoding="utf-8")
    test = repo / "src/test/java/OrderTest.java"
    test.parent.mkdir(parents=True)
    test.write_text(
        "\n".join(
            [
                "class OrderTest {",
                "  void ok() {",
                "    // add-order:added:create-order",
                "    // - THEN an order id is returned",
                "    assertEquals(orderId, result);",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    trivial = repo / "src/test/java/TrivialTest.java"
    trivial.write_text(
        "class TrivialTest { void t() { assertTrue(true); } // Empty assert }\n",
        encoding="utf-8",
    )
    config_path = write_config(repo)
    commit_all(repo, "change")
    before = spec.read_bytes()
    head = __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    report, code = run_review(load_config(config_path), config_path, cli_subject="add-order")
    by_title = {item.title: item for item in report.requirements}
    assert code == 0
    assert by_title["Create order"].evidence[-1].status == "direct"
    assert by_title["Create order"].evidence[-1].note == "只代表找到关联，不代表验收场景已经通过"
    assert by_title["Save Order.java"].evidence[-1].status == "inferred"
    assert by_title["Quiet rule"].evidence[-1].status == "insufficient"
    assessments = {(item.requirement_id, item.scenario_name): item for item in report.scenario_assessments}
    create_id = by_title["Create order"].identifier
    assert assessments[(create_id, "Happy path")].status == "supported"
    assert assessments[(create_id, "Empty assert")].status == "gap"
    assert assessments[(by_title["Bare rule"].identifier, None)].status == "unavailable"
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    assert "不能单独证明需求已经实现" in text
    assert "只代表找到关联，不代表验收场景已经通过" in text
    assert spec.read_bytes() == before
    assert __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == head
