from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from specguard.review.risk import RISK_CLASSES
from tests.fixtures.materialize import commit_all
from tests.fixtures.review_gaps.materialize import blank_repo, write_config


def test_empty_diff_lists_nine_classes_without_claiming_the_code_is_safe(tmp_path: Path) -> None:
    repo = blank_repo(tmp_path)
    spec = repo / "openspec/changes/add-order/specs/order/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "## ADDED Requirements\n\n### Requirement: Create order\n\n系统必须创建订单并且保留记录。\n",
        encoding="utf-8",
    )
    config_path = write_config(repo)
    commit_all(repo, "change")
    config = load_config(config_path)
    config.git.base = "HEAD"
    report, code = run_review(config, config_path, cli_subject="add-order")
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    assert code == 0
    assert [item.risk_class for item in report.metadata.risk_dispositions] == list(RISK_CLASSES)
    assert {item.disposition for item in report.metadata.risk_dispositions} == {"missing_context"}
    assert "这些类别已检查。未发现问题不等于代码安全。" in text
