import re
from pathlib import Path

from specguard.models.entities import ChangedFile, CheckResult, Finding, Location
from specguard.models.status import CheckStatus

EMPTY_CATCH = re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}")
BOUNDARY = re.compile(r"<=\s*[\w.]+\.(?:size|length)\(\)")
PUBLIC_METHOD = re.compile(r"^\s*public\s+[\w<>\[\], ?]+\s+\w+\s*\(")


def _location(path: str, start: int | None, end: int | None) -> Location | None:
    if start is None or start <= 0:
        return None
    return Location(file=path, line_start=start, line_end=end or start)


def review_risks(changed_files: list[ChangedFile], read_text) -> list[Finding]:
    findings: list[Finding] = []
    for changed in changed_files:
        text = read_text(changed.path) if read_text else ""
        lines = text.splitlines()
        ranges = changed.line_ranges or []
        numbers = []
        for item in ranges:
            numbers.extend(range(item.start, item.end + 1))
        if not numbers:
            findings.append(
                Finding(
                    category="business_logic",
                    severity="low",
                    summary=f"{changed.path} 缺少精确行范围，不能据此判定缺陷",
                    evidence_status="insufficient",
                    origin="risk",
                    location=None,
                )
            )
            continue
        for number in numbers:
            if number <= 0 or number > len(lines):
                continue
            line = lines[number - 1]
            if EMPTY_CATCH.search(line):
                findings.append(
                    Finding(
                        category="business_logic",
                        severity="high",
                        summary="空的 catch 会吞掉异常",
                        failure_path="异常被空 catch 吃掉后，调用方会以为操作已经成功。",
                        evidence_status="confirmed",
                        origin="risk",
                        location=_location(changed.path, number, number),
                    )
                )
            if BOUNDARY.search(line):
                findings.append(
                    Finding(
                        category="business_logic",
                        severity="high",
                        summary="边界比较可能在集合长度上越界",
                        failure_path="当索引等于集合大小时，访问会越界。",
                        evidence_status="confirmed",
                        origin="risk",
                        location=_location(changed.path, number, number),
                    )
                )
            if PUBLIC_METHOD.search(line):
                findings.append(
                    Finding(
                        category="regression",
                        severity="medium",
                        summary="公开方法签名发生变化，存在潜在的兼容性风险",
                        evidence_status="insufficient",
                        origin="risk",
                        location=_location(changed.path, number, number),
                        failure_path=None,
                    )
                )
    return findings


def existing_test_failure_note(check: CheckResult, changed_paths: set[str]) -> Finding | None:
    if check.check_id != "tests" or check.status != CheckStatus.FAIL:
        return None
    mentioned = [path for path in changed_paths if path and path in (check.diagnostic or "")]
    attributed = bool(mentioned)
    summary = "审核期间既有测试失败。"
    if not attributed:
        summary += "没有证据支持把失败算到这次修改上。"
    return Finding(
        category="test_adequacy",
        severity="high",
        summary=summary,
        failure_path="测试命令返回非零状态。" if attributed else None,
        evidence_status="confirmed" if attributed else "insufficient",
        origin="tests",
        attributes_cause=attributed,
    )
