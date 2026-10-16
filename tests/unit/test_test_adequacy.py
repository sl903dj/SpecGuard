from specguard.models.entities import ChangedFile, CheckResult, LineRange, Requirement
from specguard.models.status import CheckStatus
from specguard.review.test_adequacy import assess_tests


def _requirement() -> Requirement:
    return Requirement(
        identifier="add-order:added:create-order",
        title="Create order",
        change_semantics="added",
        source_file="spec.md",
        source_line=1,
        body="The system MUST create an order when asked by the caller.",
    )


def test_passing_tests_do_not_satisfy_requirements() -> None:
    requirement = _requirement()
    before = [item.status for item in requirement.evidence]
    _findings, coverage = assess_tests(
        [requirement],
        [ChangedFile(path="src/Order.java", change_type="modified", line_ranges=[LineRange(start=1, end=1)])],
        read_text=lambda _path: "if (value < 0) { return; }",
        test_check=CheckResult(check_id="tests", required=True, status=CheckStatus.PASS),
        coverage_available=False,
    )
    assert [item.status for item in requirement.evidence] == before
    assert coverage is None


def test_failure_and_execution_error_are_distinct() -> None:
    failed, _coverage = assess_tests(
        [],
        [],
        read_text=lambda _path: "",
        test_check=CheckResult(check_id="tests", required=True, status=CheckStatus.FAIL),
        coverage_available=False,
    )
    errored, _coverage = assess_tests(
        [],
        [],
        read_text=lambda _path: "",
        test_check=CheckResult(check_id="tests", required=True, status=CheckStatus.ERROR),
        coverage_available=False,
    )
    assert any(item.summary == "测试发现失败" for item in failed)
    assert any(item.summary == "测试未能执行" for item in errored)


def test_missing_boundary_evidence_is_reported() -> None:
    findings, coverage = assess_tests(
        [],
        [ChangedFile(path="src/Order.java", change_type="modified")],
        read_text=lambda _path: "if (value < 0 || value == null) { return; }",
        test_check=None,
        coverage_available=False,
    )
    assert any("边界" in item.summary for item in findings)
    assert coverage is None
