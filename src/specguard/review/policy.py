from specguard.config.models import ReviewConfig
from specguard.models.entities import CheckResult, Finding
from specguard.models.status import CheckStatus, ReviewStatus


def _blocking(findings: list[Finding], review: ReviewConfig) -> list[Finding]:
    allowed = set(review.severity_thresholds.block_on)
    selected: list[Finding] = []
    for finding in findings:
        if finding.evidence_status != "confirmed":
            continue
        if finding.origin.startswith("assisted"):
            continue
        if finding.severity not in allowed:
            continue
        selected.append(finding)
    return selected


def decide(
    review: ReviewConfig,
    findings: list[Finding],
    checks: list[CheckResult],
) -> tuple[ReviewStatus, bool, list[str]]:
    incomplete = any(
        item.required and item.status in {CheckStatus.SKIPPED, CheckStatus.ERROR, CheckStatus.TIMEOUT}
        for item in checks
    )
    if incomplete:
        return ReviewStatus.REVIEW_INCOMPLETE, False, ["必需检查未完成"]
    blocking = _blocking(findings, review)
    if review.policy == "strict" and blocking:
        return (
            ReviewStatus.POLICY_BLOCKED,
            True,
            [item.finding_id or item.summary for item in blocking],
        )
    return ReviewStatus.REVIEW_COMPLETE, False, []
