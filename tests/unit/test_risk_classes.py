from specguard.models.entities import ChangedFile, LineRange
from specguard.review.risk import RISK_CLASSES, review_risk_report


def _file(content: str) -> ChangedFile:
    return ChangedFile(
        path="src/Order.java",
        change_type="modified",
        line_ranges=[LineRange(start=1, end=max(content.count("\n"), 1))],
    )


def test_confirmed_patterns_cover_their_class_and_all_nine_are_reported() -> None:
    samples = {
        "exception": "class Order {\n    public void pay() { try { pay(); } catch (Exception e) {} }\n}\n",
        "null_empty": "class Order {\n    void pay(String value) { if (value == null) {} }\n}\n",
        "boundary": "class Order {\n    int bad(java.util.List items) { return 0 <= items.size(); }\n}\n",
    }
    for risk_class, content in samples.items():
        findings, dispositions = review_risk_report([_file(content)], lambda _path: content)
        confirmed = [
            item for item in findings if item.evidence_status == "confirmed" and item.risk_class == risk_class
        ]
        assert confirmed, risk_class
        assert confirmed[0].location is not None
        assert confirmed[0].location.line_start > 0
        assert confirmed[0].failure_path
        assert [item.risk_class for item in dispositions] == list(RISK_CLASSES)


def test_file_level_dependency_change_does_not_invent_line_one() -> None:
    changed = ChangedFile(path="pom.xml", change_type="modified")
    findings, dispositions = review_risk_report([changed], lambda _path: "<project></project>\n")
    assert all(item.disposition == "missing_context" for item in dispositions)
    assert not any(
        item.risk_class == "dependency_config" and item.location is not None and item.location.line_start == 1
        for item in findings
    )


def test_empty_diff_lists_every_class_as_missing_context() -> None:
    _findings, dispositions = review_risk_report([], lambda _path: "")
    assert [item.risk_class for item in dispositions] == list(RISK_CLASSES)
    assert {item.disposition for item in dispositions} == {"missing_context"}
