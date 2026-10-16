from specguard.models.entities import ChangedFile, CheckResult, LineRange, Location
from specguard.models.status import CheckStatus
from specguard.review.risk import existing_test_failure_note, review_risks
import pytest


def test_missing_lines_are_not_defects() -> None:
    changed = [ChangedFile(path="src/Order.java", change_type="modified")]
    findings = review_risks(changed, read_text=lambda _path: "class Order {}")
    assert findings
    assert all(not item.is_defect() for item in findings)
    assert all(item.location is None for item in findings)


def test_empty_catch_has_location_and_failure_path() -> None:
    text = "class Order {\n    public void pay() { try { pay(); } catch (Exception e) {} }\n}\n"
    changed = [
        ChangedFile(
            path="src/Order.java",
            change_type="modified",
            line_ranges=[LineRange(start=2, end=2)],
        )
    ]
    findings = review_risks(changed, read_text=lambda _path: text)
    defect = next(item for item in findings if item.is_defect())
    assert defect.failure_path
    assert defect.location is not None
    assert defect.location.line_start == 2


def test_line_zero_is_rejected() -> None:
    with pytest.raises(ValueError):
        Location(file="src/Order.java", line_start=0, line_end=1)


def test_existing_failure_is_not_blamed_on_this_change() -> None:
    note = existing_test_failure_note(
        CheckResult(check_id="tests", required=True, status=CheckStatus.FAIL, diagnostic="boom"),
        set(),
    )
    assert note is not None
    assert note.attributes_cause is False
    assert "由当前变更导致" not in note.summary
