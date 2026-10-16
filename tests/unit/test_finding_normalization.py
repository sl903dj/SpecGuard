from specguard.models.entities import CheckResult, Finding, Location
from specguard.models.status import CheckStatus
from specguard.review.ranking import assign_ids, conflicts_for, reliable_checks


def test_duplicates_keep_both_origins() -> None:
    location = Location(file="src/Order.java", line_start=4, line_end=4)
    findings = assign_ids(
        [
            Finding(
                category="business_logic",
                severity="high",
                summary="空的 catch 会吞掉异常",
                evidence_status="confirmed",
                origin="risk",
                location=location,
                failure_path="异常被吞掉",
            ),
            Finding(
                category="business_logic",
                severity="high",
                summary="空的 catch 会吞掉异常",
                evidence_status="confirmed",
                origin="tests",
                location=location,
                failure_path="异常被吞掉",
            ),
        ]
    )
    assert len(findings) == 2
    assert {item.origin for item in findings} == {"risk", "tests"}
    assert findings[0].duplicate_group == findings[1].duplicate_group


def test_conflicts_are_preserved() -> None:
    location = Location(file="src/Order.java", line_start=4, line_end=4)
    findings = assign_ids(
        [
            Finding(
                category="business_logic",
                severity="medium",
                summary="应当拒绝",
                evidence_status="hypothesis",
                origin="assisted_business_logic",
                location=location,
            ),
            Finding(
                category="regression",
                severity="medium",
                summary="应当接受",
                evidence_status="insufficient",
                origin="risk",
                location=location,
            ),
        ]
    )
    conflicts = conflicts_for(findings)
    assert conflicts
    assert set(conflicts[0]) == {item.finding_id for item in findings}


def test_reliable_checks_exclude_skipped_error_and_timeout() -> None:
    checks = [
        CheckResult(check_id="build", required=True, status=CheckStatus.PASS),
        CheckResult(check_id="tests", required=True, status=CheckStatus.FAIL),
        CheckResult(check_id="checkstyle", required=False, status=CheckStatus.SKIPPED),
        CheckResult(check_id="pmd", required=False, status=CheckStatus.ERROR),
        CheckResult(check_id="spotbugs", required=False, status=CheckStatus.TIMEOUT),
        CheckResult(check_id="assisted_business_logic", required=False, status=CheckStatus.PASS),
    ]
    assert reliable_checks(checks) == ["build", "tests"]
