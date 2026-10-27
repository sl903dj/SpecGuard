import json
from pathlib import Path

from specguard.llm.redact import redact
from specguard.models.entities import CalibrationView


def _review_complete(review: dict) -> bool:
    subject = review.get("subject_id")
    finding_ids = review.get("finding_ids")
    verdicts = review.get("verdicts")
    misses = review.get("misses")
    no_misses = review.get("no_misses")
    if not isinstance(subject, str) or not subject.strip():
        return False
    if not isinstance(finding_ids, list) or not all(isinstance(item, str) and item for item in finding_ids):
        return False
    if not isinstance(verdicts, list) or not isinstance(misses, list):
        return False
    if not isinstance(no_misses, bool):
        return False
    if no_misses == bool(misses):
        return False
    seen: dict[str, str] = {}
    allowed = set(finding_ids)
    for verdict in verdicts:
        if not isinstance(verdict, dict):
            return False
        finding_id = verdict.get("finding_id")
        kind = verdict.get("verdict")
        if finding_id not in allowed or kind not in {"true_issue", "false_positive"}:
            return False
        previous = seen.get(finding_id)
        if previous is not None and previous != kind:
            return False
        if previous is not None:
            return False
        seen[finding_id] = kind
    return set(seen) == allowed


def _unmatched_notes(reviews: list[dict]) -> list[str]:
    notes: list[str] = []
    for review in reviews:
        finding_ids = review.get("finding_ids")
        allowed = set(finding_ids) if isinstance(finding_ids, list) else set()
        verdicts = review.get("verdicts")
        if not isinstance(verdicts, list):
            continue
        for verdict in verdicts:
            if not isinstance(verdict, dict):
                continue
            finding_id = verdict.get("finding_id")
            kind = verdict.get("verdict")
            if kind not in {"true_issue", "false_positive"}:
                continue
            if isinstance(finding_id, str) and finding_id in allowed:
                continue
            label = finding_id if isinstance(finding_id, str) and finding_id else "未命名结论"
            note = f"无法对应到发现: {label}"
            if note not in notes:
                notes.append(note)
    return notes


def _with_unmatched(notes: list[str], unmatched: list[str]) -> list[str]:
    return [*notes, *[note for note in unmatched if note not in notes]]


def _unusable(redactions: list[dict]) -> tuple[CalibrationView, list[dict]]:
    return (
        CalibrationView(status="incomplete", notes=["对照记录不可用"]),
        redactions,
    )


def load_calibration(report_dir: Path) -> tuple[CalibrationView, list[dict]]:
    root = report_dir.resolve()
    path = (root / "calibration.json").resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return _unusable([])
    if not path.is_file():
        return CalibrationView(status="incomplete", notes=["历史对照未完成"]), []
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _unusable([])
    _cleaned, redactions = redact(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("reviews"), list):
        return _unusable(redactions)
    reviews = payload["reviews"]
    if any(not isinstance(item, dict) for item in reviews):
        return _unusable(redactions)
    try:
        completed = sum(1 for item in reviews if _review_complete(item))
        invalid = any(isinstance(item, dict) and _contradicts(item) for item in reviews)
    except (TypeError, ValueError):
        return _unusable(redactions)
    if invalid:
        return _unusable(redactions)
    unmatched = _unmatched_notes(reviews)
    if payload.get("complete") is True and completed == 0:
        return (
            CalibrationView(
                status="incomplete",
                completed_review_count=0,
                rejected_complete_mark=True,
                notes=_with_unmatched(["历史对照未完成", "完成标记已拒绝"], unmatched),
            ),
            redactions,
        )
    if payload.get("complete") is True and completed >= 1 and not unmatched:
        return (
            CalibrationView(status="complete", completed_review_count=completed, notes=[]),
            redactions,
        )
    return (
        CalibrationView(
            status="incomplete",
            completed_review_count=completed,
            notes=_with_unmatched(["历史对照未完成"], unmatched),
        ),
        redactions,
    )


def _contradicts(review: dict) -> bool:
    verdicts = review.get("verdicts")
    if not isinstance(verdicts, list):
        return True
    seen: dict[str, str] = {}
    for verdict in verdicts:
        if not isinstance(verdict, dict):
            return True
        finding_id = verdict.get("finding_id")
        kind = verdict.get("verdict")
        if not isinstance(finding_id, str) or kind not in {"true_issue", "false_positive"}:
            return True
        previous = seen.get(finding_id)
        if previous is not None and previous != kind:
            return True
        seen[finding_id] = kind
    misses = review.get("misses")
    no_misses = review.get("no_misses")
    if isinstance(no_misses, bool) and isinstance(misses, list) and no_misses and misses:
        return True
    return False
