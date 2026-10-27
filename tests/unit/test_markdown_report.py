from specguard.models.entities import (
    ArtifactContextEntry,
    ArtifactReport,
    CalibrationView,
    ChangedFile,
    ConsistencyItem,
    Evidence,
    Finding,
    Metadata,
    PolicyView,
    Requirement,
    ReviewReport,
    Summary,
    TaskItem,
)
from specguard.models.status import ReviewStatus
from specguard.report.markdown import render_markdown


def _report(provider: str) -> ReviewReport:
    subject = "003-demo" if provider == "speckit" else "add-order"
    return ReviewReport(
        review_status=ReviewStatus.REVIEW_COMPLETE,
        policy=PolicyView(mode="advisory", blocked=False),
        metadata=Metadata(
            tool_version="0.2.0",
            config_version=1,
            repository_root="/repo",
            base="abc",
            target="def",
            head_sha="def",
            change=subject,
            artifact_provider=provider,
            subject_id=subject,
            selection_source="config",
            started_at="t0",
            finished_at="t1",
        ),
        summary=Summary(needs_human_review=False),
        artifacts=ArtifactReport(
            available=True,
            provider=provider,
            subject_id=subject,
            selection_source="config",
            found=["spec.md"],
            missing=["tasks.md"],
            context_documents=[ArtifactContextEntry(kind="plan", path=f"specs/{subject}/plan.md")],
            selected_change=subject,
        ),
        tasks=[
            TaskItem(
                identifier="T001",
                text="实现功能",
                marked_complete=True,
                source_file=f"specs/{subject}/tasks.md",
                source_line=4,
                support="none",
            )
        ],
    )


def test_summary_states_evidence_conflicts_calibration_and_risk_in_order() -> None:
    report = _report("openspec")
    report.requirements = [
        Requirement(
            identifier="order:create-order",
            title="Create order",
            change_semantics="added",
            source_file="openspec/changes/add-order/specs/order/spec.md",
            source_line=3,
            evidence=[
                Evidence(
                    status="insufficient",
                    requirement_id="order:create-order",
                    note="找不到实现证据",
                )
            ],
        )
    ]
    report.consistency_items = [
        ConsistencyItem(
            capability="order",
            current_requirement_id="order:create-order",
            current_file="openspec/specs/order/spec.md",
            current_line=4,
            change_requirement_id="add-order:added:create-order",
            change_file="openspec/changes/add-order/specs/order/spec.md",
            change_line=8,
            status="conflict",
            summary="变更否定了当前规范中仍然有效的场景，且没有声明修改或删除",
        ),
        ConsistencyItem(
            capability="order",
            current_requirement_id="order:ship-notice",
            current_file="openspec/specs/order/spec.md",
            current_line=12,
            change_requirement_id="add-order:added:ship-notice",
            change_file="openspec/changes/add-order/specs/order/spec.md",
            change_line=20,
            status="human_review",
            summary="无法判断是否冲突",
        ),
    ]
    report.metadata.calibration = CalibrationView(status="incomplete", notes=["历史对照未完成"])
    report.summary.highest_risks = ["F003"]
    report.findings = [
        Finding(
            finding_id="F003",
            category="business_logic",
            severity="high",
            summary="空的 catch 会吞掉异常",
            failure_path="异常被空 catch 吃掉后，调用方会以为操作已经成功。",
            evidence_status="confirmed",
            origin="risk",
        )
    ]
    text = render_markdown(report)
    weak = text.index("- 最弱需求证据: insufficient")
    conflicts = text.index("- 未声明冲突数量: 1")
    calibration = text.index("- 历史对照未完成")
    risk = text.index("- 应先看的最高风险: F003")
    assert weak < conflicts < calibration < risk


def test_markdown_renders_neutral_artifact_metadata() -> None:
    text = render_markdown(_report("speckit"))
    assert "工件提供方: speckit" in text
    assert "审核对象: 003-demo" in text
    assert "选择来源: config" in text
    assert "已找到工件: spec.md" in text
    assert "缺失工件: tasks.md" in text
    assert "需求总数: 0" in text
    assert "任务 T001: 已完成 支撑 none @ specs/003-demo/tasks.md:4" in text
    assert "上下文 plan: specs/003-demo/plan.md" in text
    assert "缺少 OpenSpec" not in text
    assert "长期规范" not in text


def test_markdown_distinguishes_current_spec_from_change() -> None:
    current = _report("openspec")
    current.metadata.change = None
    current.metadata.subject_id = "current"
    current.metadata.subject_kind = "current"
    current.metadata.tasks_available = False
    current.artifacts.subject_id = "current"
    current.artifacts.subject_kind = "current"
    current.artifacts.tasks_available = False
    current.artifacts.selected_change = None
    current.artifacts.found = ["specs/order/spec.md"]
    current.artifacts.missing = []
    current.tasks = []
    text = render_markdown(current)
    assert "当前规范" in text
    assert "任务完整性不可用" in text
    assert "任务完整性缺口" not in text
    assert "proposal.md" not in text
    assert "tasks.md" not in text

    change = _report("openspec")
    change.metadata.subject_kind = "change"
    change.artifacts.subject_kind = "change"
    text = render_markdown(change)
    assert "进行中的变更" in text
    assert "任务完整性缺口" in text
    assert "当前规范" not in text


def test_markdown_states_when_current_spec_range_has_no_code_or_tests() -> None:
    report = _report("openspec")
    report.metadata.subject_kind = "current"
    report.metadata.subject_id = "current"
    report.metadata.change = None
    report.metadata.tasks_available = False
    report.artifacts.subject_kind = "current"
    report.artifacts.subject_id = "current"
    report.artifacts.tasks_available = False
    report.artifacts.selected_change = None
    report.changed_files = [
        ChangedFile(path="openspec/specs/order/spec.md", change_type="modified")
    ]
    report.requirements = [
        Requirement(
            identifier="order:create-order",
            title="Create order",
            change_semantics=None,
            capability="order",
            source_file="openspec/specs/order/spec.md",
            source_line=3,
        )
    ]
    report.summary.insufficient_count = 1
    text = render_markdown(report)
    assert "选定版本范围内没有可核验证据" in text
    assert "order:create-order: insufficient" in text


def test_markdown_uses_provider_specific_completeness_label() -> None:
    speckit = render_markdown(_report("speckit"))
    openspec = render_markdown(_report("openspec"))
    assert "Spec Kit 工件完整性" in speckit
    assert "OpenSpec 工件完整性" in openspec
