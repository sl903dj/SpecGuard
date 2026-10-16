import re

from specguard.models.entities import ChangedFile, CheckResult, Finding, Requirement
from specguard.models.status import CheckStatus

BOUNDARY_HINT = re.compile(r"<|>|null|Null")
BOUNDARY_TEST = ("null", "empty", "边界", "negative", "异常", "边界条件")


def assess_tests(
    requirements: list[Requirement],
    changed_files: list[ChangedFile],
    read_text,
    test_check: CheckResult | None,
    coverage_available: bool,
) -> tuple[list[Finding], float | None]:
    before = [[ev.status for ev in item.evidence] for item in requirements]
    findings: list[Finding] = []
    if test_check is not None and test_check.status == CheckStatus.FAIL:
        findings.append(
            Finding(
                category="test_adequacy",
                severity="high",
                summary="测试发现失败",
                failure_path="测试命令失败，这与测试进程未能执行不同。",
                evidence_status="confirmed",
                origin="tests",
            )
        )
    elif test_check is not None and test_check.status in {CheckStatus.ERROR, CheckStatus.TIMEOUT}:
        findings.append(
            Finding(
                category="test_adequacy",
                severity="high",
                summary="测试未能执行",
                failure_path="测试命令没有成功跑完。",
                evidence_status="confirmed",
                origin="tests",
            )
        )
    code_bits = []
    test_bits = []
    for changed in changed_files:
        text = read_text(changed.path) if read_text else ""
        if "/test/" in changed.path.lower() or changed.path.lower().endswith("test.java"):
            test_bits.append(text.lower())
        else:
            code_bits.append(text)
    if any(BOUNDARY_HINT.search(bit or "") for bit in code_bits) and not any(
        word in " ".join(test_bits) for word in BOUNDARY_TEST
    ):
        findings.append(
            Finding(
                category="test_adequacy",
                severity="medium",
                summary="缺少边界、反向或异常场景的测试证据",
                failure_path="变更代码包含比较或空值处理，但测试里看不到对应场景。",
                evidence_status="insufficient",
                origin="test_adequacy",
            )
        )
    after = [[ev.status for ev in item.evidence] for item in requirements]
    if before != after:
        raise RuntimeError("测试通过不得改写需求证据")
    return findings, None
