from specguard.models.entities import ChangedFile, Requirement, TaskItem
from specguard.review.traceability import link_requirements, link_tasks


def _requirement(semantics: str = "added", body: str = "Create an order record") -> Requirement:
    return Requirement(
        identifier="add-order:added:create-order",
        title="Create order",
        change_semantics=semantics,  # type: ignore[arg-type]
        source_file="spec.md",
        source_line=3,
        body=body,
    )


def test_file_overlap_is_only_inferred() -> None:
    requirement = _requirement(body="see Order.java for the flow of creating an order record")
    changed = [ChangedFile(path="src/Order.java", change_type="added")]
    link_requirements([requirement], changed, read_text=lambda _path: "class Order {}")
    assert requirement.evidence[-1].status == "inferred"


def test_identifier_in_file_is_direct() -> None:
    requirement = _requirement()
    changed = [ChangedFile(path="src/Order.java", change_type="modified")]

    def read_text(_path: str) -> str:
        return "marker add-order:added:create-order"

    link_requirements([requirement], changed, read_text)
    assert requirement.evidence[-1].status == "direct"


def test_missing_evidence_is_not_a_defect() -> None:
    requirement = _requirement()
    findings = link_requirements([requirement], [], read_text=lambda _path: "")
    assert requirement.evidence[-1].status == "insufficient"
    assert "代码一定有错" not in requirement.evidence[-1].note
    assert all("代码一定有错" not in item.summary for item in findings)


def test_completed_task_without_support_is_a_gap() -> None:
    task = TaskItem(
        identifier="1.1",
        text="Add create order endpoint",
        marked_complete=True,
        source_file="tasks.md",
        source_line=2,
    )
    findings = link_tasks([task], [], read_text=lambda _path: "")
    assert task.support == "none"
    assert findings[0].category == "task_integrity"
    assert "代码一定有错" not in findings[0].summary


def test_untraceable_change_is_possible_expansion() -> None:
    requirement = _requirement()
    changed = [ChangedFile(path="src/SecretBackdoor.java", change_type="added")]
    findings = link_requirements([requirement], changed, read_text=lambda _path: "class Secret {}")
    assert any("擅自扩展" in item.summary for item in findings)
    assert all(item.evidence_status != "confirmed" for item in findings)


def test_removed_requirement_is_not_a_defect() -> None:
    requirement = _requirement("removed")
    findings = link_requirements([requirement], [], read_text=lambda _path: "")
    assert findings == []
    assert "实现缺陷" not in requirement.evidence[-1].note
