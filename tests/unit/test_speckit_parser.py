from pathlib import Path

from specguard.speckit.parser import load_feature, parse_spec


SPEC = """# 示例

### User Story 1 - 创建订单 (Priority: P1)

1. **Given** 有商品, **When** 下单, **Then** 得到单号

- **FR-001**: 系统必须创建订单
"""


def test_parser_reads_requirements_stories_and_scenarios() -> None:
    requirements = parse_spec(SPEC, "specs/001-sample/spec.md")
    identifiers = [item.identifier for item in requirements]
    assert "FR-001" in identifiers
    story = next(item for item in requirements if item.identifier == "创建订单")
    assert story.scenarios
    assert story.scenarios[0].name == "得到单号"
    fr = next(item for item in requirements if item.identifier == "FR-001")
    assert fr.source_line > 0


def test_empty_spec_does_not_invent_requirements(tmp_path: Path) -> None:
    feature = tmp_path / "001-empty"
    feature.mkdir()
    (feature / "spec.md").write_text("# 只有标题\n", encoding="utf-8")
    artifacts, requirements, _tasks = load_feature(feature, "001-empty")
    assert requirements == []
    assert artifacts.available is False
    assert [item.identifier for item in requirements] == []
