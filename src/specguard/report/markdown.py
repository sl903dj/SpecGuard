from specguard.models.entities import DISCLAIMER, ReviewReport
from specguard.models.status import ReviewStatus


def _status_heading(report: ReviewReport) -> str:
    return f"**状态**: {report.review_status.value}"


def render_markdown(report: ReviewReport) -> str:
    lines = [
        "# 变更质量报告",
        "",
        _status_heading(report),
        "",
        "## 需要人工审核",
        "",
    ]
    if report.summary.needs_human_review:
        lines.append("有证据不足、含糊需求、模型假设或互相冲突的结论，需要工程师复核。")
    else:
        lines.append("没有额外的人工复核提示。这仍然不是代码安全的证明。")
    lines.extend(["", "## 需求覆盖", ""])
    if not report.artifacts.available:
        lines.append("基于需求的审核不可用。")
    lines.append(f"- 直接证据: {report.summary.direct_count}")
    lines.append(f"- 仅有推断: {report.summary.inferred_count}")
    lines.append(f"- 证据不足: {report.summary.insufficient_count}")
    lines.append(f"- 任务完整性缺口: {report.summary.task_gap_count}")
    lines.extend(["", "## 潜在风险", ""])
    if report.summary.highest_risks:
        for item in report.summary.highest_risks:
            finding = next(found for found in report.findings if found.finding_id == item)
            place = "位置不可用" if finding.location is None else (
                f"{finding.location.file}:{finding.location.line_start}"
            )
            lines.append(f"- {finding.finding_id} {finding.summary} ({place}, {finding.evidence_status})")
    else:
        lines.append("没有形成风险条目。")
    lines.extend(["", "## 证据定位", ""])
    if not report.findings and not report.requirements:
        lines.append("当前没有可定位的需求或发现。")
    for finding in report.findings:
        lines.append(f"- {finding.finding_id}: 来源 {finding.origin}")
    for requirement in report.requirements:
        status = requirement.evidence[-1].status if requirement.evidence else "insufficient"
        lines.append(f"- 需求 {requirement.identifier}: {status} @ {requirement.source_file}:{requirement.source_line}")
    lines.extend(["", "## 检查结果", ""])
    if not report.checks:
        lines.append("实际执行的检查：无")
    for check in report.checks:
        lines.append(
            f"- {check.check_id}: {check.status.value} command={check.command} duration={check.duration_seconds} exit={check.exit_code}"
        )
    if report.summary.reliable_checks:
        lines.append("")
        lines.append("已有可靠证据、不必反复人工确认的检查: " + ", ".join(report.summary.reliable_checks))
    lines.extend(["", "## 限制说明", "", DISCLAIMER, ""])
    if not report.findings:
        names = ", ".join(item.check_id for item in report.checks) or "无"
        lines.append(f"本次没有发现并不表示代码没有缺陷。实际执行的检查：{names}")
    if report.review_status == ReviewStatus.REVIEW_INCOMPLETE:
        lines.append("本次审核不完整，不能当成全部检查已通过。")
    return "\n".join(lines) + "\n"
