import re

from specguard.models.entities import ChangedFile, CheckResult, Finding, Location, Requirement
from specguard.models.status import CheckStatus

BOUNDARY_HINT = re.compile(r"<|>|null|Null")
BOUNDARY_TEST = ("null", "empty", "边界", "negative", "异常", "边界条件")
ASSERTION = re.compile(r"assert(?:True|False|Equals|NotNull|Null|That)\s*\(([^;]*)\)", re.I)


def _trivial_assertion(args: str) -> bool:
    compact = re.sub(r"\s+", "", args)
    if compact.lower() in {"true", "false"}:
        return True
    if compact.lower() in {"newobject()"} or re.fullmatch(r"new\w+\(\)", compact):
        return True
    if "," not in compact:
        return False
    left, right = compact.split(",", 1)
    return left.lower() == right.lower() and bool(
        re.fullmatch(r"(?:true|false|null|\d+|\".*\")", left, re.I)
    )


def _simple_assertion_findings(
    requirements: list[Requirement],
    changed_files: list[ChangedFile],
    read_text,
) -> list[Finding]:
    findings: list[Finding] = []
    for changed in changed_files:
        text = read_text(changed.path) if read_text else ""
        if "/test/" not in changed.path.lower() and not changed.path.lower().endswith("test.java"):
            continue
        matches = list(ASSERTION.finditer(text))
        if not matches or not all(_trivial_assertion(item.group(1)) for item in matches):
            continue
        related = [
            item.identifier
            for item in requirements
            if item.identifier in text or item.title.lower() in text.lower()
        ]
        if not related:
            related = [
                item.identifier
                for item in requirements
                if not item.evidence or item.evidence[-1].status == "insufficient"
            ]
        line = text.count("\n", 0, matches[0].start()) + 1
        findings.append(
            Finding(
                category="test_adequacy",
                severity="medium",
                summary="测试只有不能验证需求的简单断言",
                failure_path="断言两侧都是常量，不能证明需求行为。",
                evidence_status="insufficient",
                origin="test_adequacy",
                location=Location(file=changed.path, line_start=line, line_end=line),
                related_requirement_ids=related,
            )
        )
    return findings


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
    findings.extend(_simple_assertion_findings(requirements, changed_files, read_text))
    after = [[ev.status for ev in item.evidence] for item in requirements]
    if before != after:
        raise RuntimeError("测试通过不得改写需求证据")
    return findings, None
