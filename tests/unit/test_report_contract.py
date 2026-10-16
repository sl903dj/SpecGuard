from specguard.models.entities import (
    DISCLAIMER,
    CheckResult,
    Finding,
    Location,
    Metadata,
    PolicyView,
    ReviewReport,
    Summary,
)
from specguard.models.status import CheckStatus, ReviewStatus
from specguard.report.json_report import render_json
from specguard.report.markdown import render_markdown

REQUIRED = {
    "schema_version",
    "review_status",
    "policy",
    "metadata",
    "summary",
    "changed_files",
    "requirements",
    "tasks",
    "checks",
    "findings",
    "conflicts",
    "artifacts",
}


def _report(status: ReviewStatus = ReviewStatus.REVIEW_COMPLETE) -> ReviewReport:
    return ReviewReport(
        review_status=status,
        policy=PolicyView(mode="advisory", blocked=False),
        metadata=Metadata(
            tool_version="0.1.0",
            config_version=1,
            repository_root="/repo",
            base="abc",
            target="def",
            head_sha="def",
            change=None,
            started_at="t0",
            finished_at="t1",
        ),
        summary=Summary(needs_human_review=False),
    )


def test_json_keeps_required_keys_and_version() -> None:
    payload = render_json(_report())
    assert payload["schema_version"] == "1.0"
    assert REQUIRED <= set(payload)
    assert payload["summary"]["coverage_percent"] is None
    assert payload["summary"]["disclaimer"] == DISCLAIMER


def test_empty_report_does_not_claim_the_code_is_clean() -> None:
    text = render_markdown(_report())
    assert "需要人工审核" in text
    assert "需求覆盖" in text
    assert "潜在风险" in text
    assert "证据定位" in text
    assert DISCLAIMER in text
    assert "并不表示代码没有缺陷" in text
    assert "实际执行的检查" in text
    assert "干净通过" not in text


def test_markdown_risks_and_checks_match_json_fields() -> None:
    report = _report()
    report.summary.highest_risks = ["SG-business_logic-1", "SG-regression-2"]
    report.findings = [
        Finding(
            finding_id="SG-business_logic-1",
            category="business_logic",
            severity="high",
            summary="空的 catch 会吞掉异常",
            failure_path="异常被空 catch 吃掉后，调用方会以为操作已经成功。",
            evidence_status="confirmed",
            origin="risk",
            location=Location(file="src/Order.java", line_start=4, line_end=4),
        ),
        Finding(
            finding_id="SG-regression-2",
            category="regression",
            severity="medium",
            summary="依赖变化未被核实",
            evidence_status="insufficient",
            origin="risk",
        ),
    ]
    report.checks = [
        CheckResult(
            check_id="build",
            required=True,
            status=CheckStatus.FAIL,
            command="./mvnw package",
            duration_seconds=1.5,
            exit_code=1,
            diagnostic="COMPILATION ERROR",
        )
    ]
    text = render_markdown(report)
    payload = render_json(report)
    assert "异常被空 catch 吃掉后，调用方会以为操作已经成功。" in text
    assert "SG-regression-2 依赖变化未被核实" in text
    assert "失败路径不可用" in text
    assert "SG-business_logic-1: 来源 risk @ src/Order.java:4" in text
    assert "SG-regression-2: 来源 risk @ 位置不可用" in text
    assert "diagnostic=COMPILATION ERROR" in text
    assert payload["checks"][0]["diagnostic"] == "COMPILATION ERROR"
    assert payload["findings"][1]["failure_path"] is None


def test_incomplete_report_is_not_a_clean_pass() -> None:
    text = render_markdown(_report(ReviewStatus.REVIEW_INCOMPLETE))
    assert "REVIEW_INCOMPLETE" in text
    assert "不能当成全部检查已通过" in text
    assert "干净通过" not in text
