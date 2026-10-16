from pathlib import Path

from specguard.checks.test_results import parse_test_result_file
from specguard.models.entities import (
    ChangedFile,
    LineRange,
    Metadata,
    PolicyView,
    Requirement,
    ReviewReport,
    Summary,
)
from specguard.models.status import ReviewStatus
from specguard.openspec.parser import load_change
from specguard.report.markdown import render_markdown
from specguard.report.snippets import limited_snippets
from specguard.review.assisted import build_context
from specguard.review.risk import missing_logic_context, review_risks
from specguard.review.test_adequacy import assess_tests
from specguard.models.status import CheckStatus
from specguard.models.entities import CheckResult


def _report() -> ReviewReport:
    return ReviewReport(
        review_status=ReviewStatus.REVIEW_COMPLETE,
        policy=PolicyView(mode="advisory", blocked=False),
        metadata=Metadata(
            tool_version="0.1.0",
            config_version=1,
            repository_root="/repo",
            base="abc",
            target="def",
            head_sha="def",
            change="add-order",
            started_at="t0",
            finished_at="t1",
            modules=["."],
        ),
        summary=Summary(needs_human_review=True),
        requirements=[
            Requirement(
                identifier="add-order:added:create-order",
                title="Create order",
                change_semantics="added",
                source_file="spec.md",
                source_line=3,
                body="TBD",
                ambiguous=True,
                ambiguity_reason="需求信息不足或含糊，无法可靠核验",
            )
        ],
    )


def test_markdown_shows_ambiguity_modules_and_unavailable_coverage() -> None:
    text = render_markdown(_report())
    assert "含糊需求 add-order:added:create-order: 需求信息不足或含糊，无法可靠核验" in text
    assert "识别到的构建模块: ." in text
    assert "覆盖率分析不可用" in text
    assert "%" not in text.split("覆盖率分析不可用")[0].split("识别到的构建模块")[-1]


def test_simple_assertions_do_not_satisfy_the_requirement() -> None:
    requirement = Requirement(
        identifier="add-order:added:create-order",
        title="Create order",
        change_semantics="added",
        source_file="spec.md",
        source_line=1,
        body="The system MUST create an order when asked by the caller.",
    )
    before = [item.status for item in requirement.evidence]
    findings, coverage = assess_tests(
        [requirement],
        [ChangedFile(path="src/test/java/OrderTest.java", change_type="added", line_ranges=[LineRange(start=1, end=1)])],
        read_text=lambda _path: 'void test() { assertTrue(true); assertEquals(1, 1); }',
        test_check=CheckResult(check_id="tests", required=False, status=CheckStatus.PASS),
        coverage_available=False,
    )
    assert [item.status for item in requirement.evidence] == before
    assert coverage is None
    finding = next(item for item in findings if "简单断言" in item.summary)
    assert finding.evidence_status == "insufficient"
    assert finding.location is not None
    assert finding.location.file.endswith("OrderTest.java")
    assert requirement.identifier in finding.related_requirement_ids


def test_missing_business_context_is_not_a_confirmed_defect() -> None:
    changed = [
        ChangedFile(
            path="src/Order.java",
            change_type="modified",
            line_ranges=[LineRange(start=1, end=1)],
        )
    ]
    text = "class Order { int pay() { return 1; } }\n"
    findings = review_risks(changed, lambda _path: text)
    assert all(not item.is_defect() for item in findings)
    assert missing_logic_context(changed, lambda _path: text)


def test_dependency_change_stays_a_hypothesis() -> None:
    changed = [
        ChangedFile(path="pom.xml", change_type="modified", line_ranges=[LineRange(start=1, end=1)])
    ]
    findings = review_risks(changed, lambda _path: "<project></project>\n")
    finding = next(item for item in findings if "依赖" in item.summary)
    assert finding.evidence_status == "insufficient"
    assert "不是已核实的不兼容" in finding.summary
    assert finding.is_defect() is False


def test_main_specs_are_parsed_into_review_context(tmp_path: Path) -> None:
    root = tmp_path / "openspec"
    change = root / "changes" / "add-order" / "specs"
    change.mkdir(parents=True)
    (change / "spec.md").write_text(
        "## ADDED Requirements\n\n### Requirement: Create order\n\nThe system MUST create an order when asked.\n\n#### Scenario: Ok\n\n- WHEN x\n- THEN y\n",
        encoding="utf-8",
    )
    main = root / "specs"
    main.mkdir()
    (main / "spec.md").write_text(
        "## Requirements\n\n### Requirement: Keep audit\n\nThe system MUST keep an audit trail for every change.\n",
        encoding="utf-8",
    )
    artifacts, requirements, _tasks = load_change(root, "add-order", True)
    assert any(item.title == "Keep audit" for item in artifacts.main_requirements)
    assert artifacts.main_requirements[0].body
    assert all(item.title != "Keep audit" for item in requirements)
    skipped, _requirements, _tasks = load_change(root, "add-order", False)
    assert skipped.main_requirements == []


def test_coverage_is_not_invented() -> None:
    assert parse_test_result_file(None) is None
    assert parse_test_result_file("tests passed")["coverage_percent"] is None
    assert parse_test_result_file("jacoco coverage 80%")["coverage_percent"] == 80.0


def test_snippets_appear_only_when_enabled_and_are_redacted() -> None:
    changed = [ChangedFile(path="src/A.java", change_type="modified")]
    text = "api_key=supersecretvalue class Order {}"
    hidden = limited_snippets(changed, lambda _path: text, False)
    shown = limited_snippets(changed, lambda _path: text, True)
    assert hidden == []
    assert shown
    assert "supersecretvalue" not in shown[0]
    assert "src/A.java" in shown[0]
    report = _report()
    report.metadata.source_snippets = shown
    rendered = render_markdown(report)
    assert "源码片段" in rendered
    assert "supersecretvalue" not in rendered
    report.metadata.source_snippets = []
    assert "源码片段" not in render_markdown(report)


def test_redaction_notes_do_not_include_the_secret() -> None:
    changed = [ChangedFile(path="src/A.java", change_type="modified")]
    text, _truncated, notes = build_context(changed, lambda _path: "api_key=supersecretvalue\n", 1000)
    assert "supersecretvalue" not in text
    assert notes
    assert notes[0]["category"] == "credential"
    assert "supersecretvalue" not in str(notes)
