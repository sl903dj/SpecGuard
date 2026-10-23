from pathlib import Path

from specguard.config.models import ReviewConfig
from specguard.llm.redact import merge_redactions, redact
from specguard.models.entities import ChangedFile, CheckResult, Finding
from specguard.models.status import CheckStatus

ASSISTED_IDS = (
    "assisted_requirements",
    "assisted_business_logic",
    "assisted_test_adequacy",
    "assisted_regression",
)


def skipped_dimensions() -> list[CheckResult]:
    return [
        CheckResult(
            check_id=name,
            required=False,
            status=CheckStatus.SKIPPED,
            diagnostic="未配置辅助审查",
        )
        for name in ASSISTED_IDS
    ]


def error_dimensions(message: str) -> list[CheckResult]:
    return [
        CheckResult(
            check_id=name,
            required=False,
            status=CheckStatus.ERROR,
            diagnostic=message,
        )
        for name in ASSISTED_IDS
    ]


def is_reviewed_principle(path: str) -> bool:
    parts = [part for part in Path(path).as_posix().split("/") if part not in {"", "."}]
    return tuple(parts[-3:]) == (".specify", "memory", "constitution.md")


def build_context(files: list[ChangedFile], read_text, max_chars: int) -> tuple[str, bool, list[dict]]:
    chunks: list[str] = []
    notes: list[dict] = []
    for item in files:
        if is_reviewed_principle(item.path):
            continue
        text = read_text(item.path) if read_text else ""
        cleaned, file_notes = redact(text)
        notes.extend(file_notes)
        chunks.append(f"## {item.path}\n{cleaned}")
    raw = "\n".join(chunks)
    merged = merge_redactions(notes)
    if len(raw) <= max_chars:
        return raw, False, merged
    return raw[:max_chars], True, merged


def review_untrusted(source: str, policy: ReviewConfig) -> ReviewConfig:
    _ = source
    return policy


_CATEGORIES = {
    "requirements",
    "task_integrity",
    "business_logic",
    "test_adequacy",
    "regression",
}
_SEVERITIES = {"critical", "high", "medium", "low", "info"}


def merge_llm_output(payload: dict, changed_paths: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for item in payload.get("findings") or []:
        path = item.get("file")
        line = item.get("line")
        location = None
        status = "hypothesis"
        if path in changed_paths and isinstance(line, int) and line > 0:
            from specguard.models.entities import Location

            location = Location(file=path, line_start=line, line_end=line)
        else:
            status = "insufficient"
        category = item.get("category")
        severity = item.get("severity")
        findings.append(
            Finding(
                category=category if category in _CATEGORIES else "business_logic",
                severity=severity if severity in _SEVERITIES else "medium",
                summary=str(item.get("summary") or "模型提出的待复核假设"),
                failure_path=item.get("failure_path"),
                evidence_status=status,  # type: ignore[arg-type]
                origin="assisted_business_logic",
                location=location,
            )
        )
    return findings
