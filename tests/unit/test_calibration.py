import json
from pathlib import Path

from specguard.config.models import ReviewConfig
from specguard.models.entities import Finding
from specguard.review.calibration import load_calibration
from specguard.review.policy import decide

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "review_gaps" / "calibration"


def _copy(tmp_path: Path, name: str | None) -> Path:
    directory = tmp_path / "reports"
    directory.mkdir(parents=True)
    if name is not None:
        (directory / "calibration.json").write_text((FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8")
    return directory


def test_ledger_states(tmp_path: Path) -> None:
    missing, _redactions = load_calibration(_copy(tmp_path / "missing", None))
    assert missing.status == "incomplete"
    assert missing.notes == ["历史对照未完成"]

    incomplete, _redactions = load_calibration(_copy(tmp_path / "incomplete", "incomplete.json"))
    assert incomplete.status == "incomplete"
    assert incomplete.completed_review_count == 0

    rejected, _redactions = load_calibration(_copy(tmp_path / "false", "false_complete.json"))
    assert rejected.status == "incomplete"
    assert rejected.rejected_complete_mark is True

    done, redactions = load_calibration(_copy(tmp_path / "done", "complete.json"))
    assert done.status == "complete"
    assert done.completed_review_count == 1
    assert redactions == []

    secret_view, redactions = load_calibration(_copy(tmp_path / "secret", "secret.json"))
    assert secret_view.status == "complete"
    assert redactions
    rendered = json.dumps(secret_view.model_dump(), ensure_ascii=False)
    assert "supersecretvalue" not in rendered


def test_unknown_finding_and_contradiction_do_not_complete(tmp_path: Path) -> None:
    unknown = {
        "complete": True,
        "reviews": [
            {
                "subject_id": "add-order",
                "finding_ids": ["F001"],
                "verdicts": [{"finding_id": "F999", "verdict": "true_issue"}],
                "misses": [],
                "no_misses": True,
            }
        ],
    }
    directory = tmp_path / "unknown"
    directory.mkdir()
    (directory / "calibration.json").write_text(json.dumps(unknown), encoding="utf-8")
    view, _redactions = load_calibration(directory)
    assert view.status == "incomplete"
    assert view.completed_review_count == 0
    assert "无法对应到发现: F999" in view.notes

    named = {
        "complete": False,
        "reviews": [
            {
                "subject_id": "add-order",
                "finding_ids": ["F001"],
                "verdicts": [
                    {"finding_id": "F001", "verdict": "true_issue"},
                    {"finding_id": "F404", "verdict": "false_positive"},
                ],
                "misses": [],
                "no_misses": True,
            }
        ],
    }
    named_dir = tmp_path / "named"
    named_dir.mkdir()
    (named_dir / "calibration.json").write_text(json.dumps(named), encoding="utf-8")
    named_view, _redactions = load_calibration(named_dir)
    assert named_view.status == "incomplete"
    assert named_view.rejected_complete_mark is False
    assert "无法对应到发现: F404" in named_view.notes

    conflict = {
        "complete": True,
        "reviews": [
            {
                "subject_id": "add-order",
                "finding_ids": ["F001"],
                "verdicts": [
                    {"finding_id": "F001", "verdict": "true_issue"},
                    {"finding_id": "F001", "verdict": "false_positive"},
                ],
                "misses": [],
                "no_misses": True,
            }
        ],
    }
    conflicted = tmp_path / "conflict"
    conflicted.mkdir()
    (conflicted / "calibration.json").write_text(json.dumps(conflict), encoding="utf-8")
    view, _redactions = load_calibration(conflicted)
    assert view.status == "incomplete"
    assert view.notes == ["对照记录不可用"]


def test_complete_calibration_does_not_make_decide_block() -> None:
    advisory = ReviewConfig(policy="advisory")
    _status, blocked, _reasons = decide(advisory, [], [])
    assert blocked is False
    hypothesis = Finding(
        category="business_logic",
        severity="high",
        summary="模型假设",
        evidence_status="hypothesis",
        origin="assisted_business_logic",
    )
    strict = ReviewConfig(policy="strict")
    _status, blocked, _reasons = decide(strict, [hypothesis], [])
    assert blocked is False
