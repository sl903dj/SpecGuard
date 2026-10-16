import re

from specguard.models.entities import CheckResult, Finding
from specguard.models.status import CheckStatus

COVERAGE = re.compile(r"(?i)(?:coverage|jacoco)[^%\n]{0,40}?(\d+(?:\.\d+)?)\s*%")


def parse_test_result_file(text: str | None) -> dict | None:
    if text is None:
        return None
    match = COVERAGE.search(text)
    percent = float(match.group(1)) if match else None
    return {"raw_present": True, "coverage_percent": percent, "body": text[:200]}


def note_missing_results(check: CheckResult | None) -> Finding | None:
    if check is None or check.status == CheckStatus.SKIPPED:
        return Finding(
            category="test_adequacy",
            severity="info",
            summary="测试结果文件不可用，未编造通过数或覆盖率",
            evidence_status="insufficient",
            origin="test_results",
        )
    return None
