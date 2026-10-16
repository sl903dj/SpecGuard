from specguard.models.entities import CheckResult, Finding
from specguard.models.status import CheckStatus


def parse_test_result_file(text: str | None) -> dict | None:
    if text is None:
        return None
    return {"raw_present": True, "coverage_percent": None, "body": text[:200]}


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
