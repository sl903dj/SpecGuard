from specguard.config.models import ReviewConfig
from specguard.models.entities import CheckResult, Finding
from specguard.models.status import CheckStatus, ReviewStatus
from specguard.review.policy import decide


def _review(policy: str) -> ReviewConfig:
    return ReviewConfig(mode="static", policy=policy, llm_findings_block=False)  # type: ignore[arg-type]


def _confirmed() -> Finding:
    return Finding(
        finding_id="SG-regression-1",
        category="regression",
        severity="high",
        summary="确定性检查 build 失败",
        failure_path="命令返回非零状态。",
        evidence_status="confirmed",
        origin="build",
    )


def _hypothesis() -> Finding:
    return Finding(
        category="business_logic",
        severity="critical",
        summary="模型假设",
        evidence_status="hypothesis",
        origin="assisted_business_logic",
    )


def test_advisory_never_blocks() -> None:
    status, blocked, _reasons = decide(
        _review("advisory"),
        [_confirmed()],
        [CheckResult(check_id="build", required=True, status=CheckStatus.FAIL)],
    )
    assert status == ReviewStatus.REVIEW_COMPLETE
    assert blocked is False


def test_strict_blocks_only_confirmed_deterministic_findings() -> None:
    status, blocked, _reasons = decide(
        _review("strict"),
        [_confirmed()],
        [CheckResult(check_id="build", required=True, status=CheckStatus.FAIL)],
    )
    assert status == ReviewStatus.POLICY_BLOCKED
    assert blocked is True
    status, blocked, _reasons = decide(
        _review("strict"),
        [_hypothesis()],
        [CheckResult(check_id="build", required=True, status=CheckStatus.PASS)],
    )
    assert blocked is False
    assert status == ReviewStatus.REVIEW_COMPLETE


def test_incomplete_required_check_outranks_block() -> None:
    status, blocked, _reasons = decide(
        _review("strict"),
        [_confirmed()],
        [CheckResult(check_id="tests", required=True, status=CheckStatus.TIMEOUT)],
    )
    assert status == ReviewStatus.REVIEW_INCOMPLETE
    assert blocked is False
