from specguard.models.entities import (
    ArtifactContextEntry,
    ArtifactReport,
    Metadata,
    PolicyView,
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


def test_markdown_uses_provider_specific_completeness_label() -> None:
    speckit = render_markdown(_report("speckit"))
    openspec = render_markdown(_report("openspec"))
    assert "Spec Kit 工件完整性" in speckit
    assert "OpenSpec 工件完整性" in openspec
