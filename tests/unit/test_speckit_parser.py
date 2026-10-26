from pathlib import Path

import pytest

from specguard.artifacts.models import ArtifactProviderConfig, ArtifactSubject
from specguard.artifacts.speckit import SpecKitProvider, parse_requirements, parse_spec_document, parse_tasks
from specguard.errors import UsageError


def test_parses_requirements_story_priority_scenarios_crlf_and_chinese() -> None:
    text = (
        "### User Story 1 - 下单 (Priority: P1)\r\n\r\n"
        "1. **Given** 用户已登录，**When** 提交订单，**Then** 创建成功。\r\n\r\n"
        "- **FR-001**: 系统必须创建订单。\r\n"
    )
    requirements = parse_requirements(text, "specs/demo/spec.md")
    requirement = requirements[0]
    assert requirement.identifier == "FR-001"
    assert requirement.change_semantics is None
    assert requirement.user_story_id == "US1"
    assert requirement.priority == "P1"
    assert requirement.source_line == 5
    assert requirement.scenarios


def test_rejects_duplicate_requirements_and_template_placeholders() -> None:
    with pytest.raises(UsageError, match="重复"):
        parse_requirements(
            "- **FR-001**: one\n- **FR-001**: two\n", "spec.md"
        )
    with pytest.raises(UsageError, match="模板"):
        parse_requirements("- **FR-001**: [NEEDS CLARIFICATION]\n", "spec.md")


def test_keeps_stories_independent_from_global_requirements() -> None:
    text = (
        "### User Story 1 - 下单 (Priority: P1)\n\n"
        "1. **Given** 已登录，**When** 下单，**Then** 成功。\n\n"
        "## Requirements\n\n"
        "- **FR-001**: 系统必须创建订单。\n"
        "- **FR-002**: US1 的退款规则。\n"
    )
    requirements, stories = parse_spec_document(text, "specs/demo/spec.md")
    assert stories[0].identifier == "US1"
    assert stories[0].priority == "P1"
    assert stories[0].scenarios
    assert requirements[0].user_story_id is None
    assert requirements[0].scenarios == []
    assert requirements[1].user_story_id == "US1"
    assert requirements[1].scenarios == []


def test_rejects_missing_requirement_id_invalid_utf8_and_template_markers(tmp_path: Path) -> None:
    with pytest.raises(UsageError, match="需求 ID"):
        parse_requirements("- **Requirement**: 没有稳定 ID\n", "spec.md")
    with pytest.raises(UsageError, match="模板"):
        parse_requirements("# Feature Specification: [FEATURE NAME]\n", "spec.md")
    feature = tmp_path / "specs" / "003-demo"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_bytes(b"# bad \xff\n")
    with pytest.raises(UsageError, match="UTF-8"):
        SpecKitProvider().load(
            ArtifactSubject(
                provider="speckit",
                subject_id="003-demo",
                directory=feature.resolve(),
                selection_source="config",
            ),
            ArtifactProviderConfig(provider="speckit", include_context=False),
        )


def test_parses_tasks_and_rejects_duplicates() -> None:
    tasks = parse_tasks(
        "- [X] T001 [P] [US1] 实现功能\n- [ ] T002 后续工作\n",
        "specs/demo/tasks.md",
    )
    assert tasks[0].marked_complete is True
    assert tasks[0].parallel is True
    assert tasks[0].user_story_id == "US1"
    assert tasks[0].text == "实现功能"
    with pytest.raises(UsageError, match="重复"):
        parse_tasks("- [ ] T001 one\n- [x] T001 two\n", "tasks.md")
