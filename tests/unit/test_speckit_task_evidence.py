from pathlib import Path

from specguard.models.entities import ChangedFile
from specguard.review.traceability import link_requirements, link_tasks
from specguard.speckit.parser import load_feature, parse_spec, parse_tasks


def test_only_standard_checkboxes_are_tasks() -> None:
    text = "- [x] T010 完成下单\n- [X] T011 另一项\n- [ ] T012 未做\n- [~] T013 忽略\n"
    items = parse_tasks(text, "tasks.md")
    assert [item.identifier for item in items] == ["T010", "T011", "T012"]
    assert [item.marked_complete for item in items] == [True, True, False]


def test_missing_tasks_file_does_not_invent_completed_work(tmp_path: Path) -> None:
    feature = tmp_path / "001-sample"
    feature.mkdir()
    (feature / "spec.md").write_text("- **FR-001**: 系统必须创建订单\n", encoding="utf-8")
    artifacts, _requirements, tasks = load_feature(feature, "001-sample")
    assert "tasks.md" in artifacts.missing
    assert tasks == []


def test_requirement_identifier_in_file_content_is_direct() -> None:
    requirements = parse_spec("- **FR-001**: 系统必须创建订单\n", "spec.md")
    changed = [ChangedFile(path="src/main/java/com/example/Order.java", change_type="added")]
    link_requirements(requirements, changed, lambda _path: "class Order { /* FR-001 */ }")
    evidence = requirements[0].evidence[0]
    assert evidence.status == "direct"


def test_filename_overlap_is_not_direct_evidence() -> None:
    requirements = parse_spec("### User Story 1 - 创建订单 (Priority: P1)\n", "spec.md")
    story = next(item for item in requirements if item.identifier == "创建订单")
    changed = [ChangedFile(path="src/main/java/创建订单.java", change_type="added")]
    link_requirements([story], changed, lambda _path: "order service")
    assert story.evidence[0].status != "direct"


def test_completed_task_without_support_is_a_gap() -> None:
    tasks = parse_tasks("- [x] T010 完成下单\n", "tasks.md")
    findings = link_tasks(tasks, [], lambda _path: "")
    assert tasks[0].support == "none"
    assert findings
    assert "缺少代码或测试支撑" in findings[0].summary
    assert "一定有错" not in findings[0].summary
