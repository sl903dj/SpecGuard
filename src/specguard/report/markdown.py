from specguard.models.entities import DISCLAIMER, ReviewReport
from specguard.models.status import ReviewStatus


def _range_has_code_or_tests(report: ReviewReport) -> bool:
    for item in report.changed_files:
        lowered = item.path.replace("\\", "/").lower()
        if lowered.endswith(".java") or "/test/" in lowered or "/tests/" in lowered:
            return True
    return False


def _status_heading(report: ReviewReport) -> str:
    return f"**状态**: {report.review_status.value}"


def _audit_summary(report: ReviewReport) -> list[str]:
    if report.requirements:
        statuses = [
            item.evidence[-1].status if item.evidence else "insufficient" for item in report.requirements
        ]
        weakest = "insufficient" if "insufficient" in statuses else "inferred" if "inferred" in statuses else "direct"
    else:
        weakest = "无"
    conflicts = sum(1 for item in report.consistency_items if item.status == "conflict")
    calibration = report.metadata.calibration
    if calibration.status == "complete":
        calibration_line = f"历史对照已完成，已对照变更数量: {calibration.completed_review_count}"
    else:
        calibration_line = "历史对照未完成"
    risk = ", ".join(report.summary.highest_risks) if report.summary.highest_risks else "无"
    return [
        f"- 最弱需求证据: {weakest}",
        f"- 未声明冲突数量: {conflicts}",
        f"- {calibration_line}",
        f"- 应先看的最高风险: {risk}",
    ]


def render_markdown(report: ReviewReport) -> str:
    lines = [
        "# 变更质量报告",
        "",
        _status_heading(report),
        "",
        "## 审核摘要",
        "",
        *_audit_summary(report),
        "",
        "## 需要人工审核",
        "",
    ]
    if report.summary.needs_human_review:
        lines.append("有证据不足、含糊需求、模型假设或互相冲突的结论，需要工程师复核。")
    else:
        lines.append("没有额外的人工复核提示。这仍然不是代码安全的证明。")
    provider = report.artifacts.provider or report.metadata.artifact_provider or "未识别"
    subject = report.artifacts.subject_id or report.metadata.subject_id or "未选择"
    selection = report.artifacts.selection_source or report.metadata.selection_source or "不可用"
    provider_label = {
        "speckit": "Spec Kit",
        "openspec": "OpenSpec",
    }.get(provider, "需求")
    lines.extend(
        [
            "",
            "## 工件来源",
            "",
            f"- 工件提供方: {provider}",
            f"- 审核对象: {subject}",
            "- 对象种类: "
            + {
                "current": "当前规范",
                "change": "进行中的变更",
                "feature": "Spec Kit 功能",
            }.get(report.artifacts.subject_kind or report.metadata.subject_kind or "", "未标明"),
            f"- 选择来源: {selection}",
            f"- 证据范围: {report.metadata.evidence_scope}",
            f"- {provider_label} 工件完整性",
            "- 已找到工件: " + (", ".join(report.artifacts.found) or "无"),
            "- 缺失工件: " + (", ".join(report.artifacts.missing) or "无"),
        ]
    )
    lines.extend(["", "## 需求覆盖", ""])
    if not report.artifacts.available:
        lines.append("基于需求的审核不可用。")
    lines.append(f"- 需求总数: {len(report.requirements)}")
    lines.append(f"- 直接证据: {report.summary.direct_count}")
    lines.append(f"- 仅有推断: {report.summary.inferred_count}")
    lines.append(f"- 证据不足: {report.summary.insufficient_count}")
    if report.requirements:
        statuses = [
            item.evidence[-1].status if item.evidence else "insufficient" for item in report.requirements
        ]
        weakest = "insufficient" if "insufficient" in statuses else "inferred" if "inferred" in statuses else "direct"
        lines.append(f"- 最弱需求证据: {weakest}")
    for assessment in report.scenario_assessments:
        place = (
            f" @ {assessment.test_file}:{assessment.test_line}"
            if assessment.status == "supported"
            else ""
        )
        name = assessment.scenario_name or "无场景"
        lines.append(f"- 场景 {assessment.requirement_id}/{name}: {assessment.status}{place}")
    kind = report.artifacts.subject_kind or report.metadata.subject_kind
    if kind == "current" and not _range_has_code_or_tests(report):
        lines.append("- 选定版本范围内没有可核验证据")
    tasks_available = report.artifacts.tasks_available and report.metadata.tasks_available
    if not tasks_available:
        lines.append("- 任务完整性不可用")
    else:
        lines.append(f"- 任务完整性缺口: {report.summary.task_gap_count}")
        if report.tasks:
            for task in report.tasks:
                state = "已完成" if task.marked_complete else "未完成"
                lines.append(
                    f"- 任务 {task.identifier}: {state} 支撑 {task.support} @ {task.source_file}:{task.source_line}"
                )
        else:
            lines.append("- 任务明细: 无")
    if report.artifacts.context_documents:
        for document in report.artifacts.context_documents:
            lines.append(f"- 上下文 {document.kind}: {document.path}")
    else:
        lines.append("- 上下文工件: 无")
    for requirement in report.requirements:
        if requirement.ambiguous and requirement.ambiguity_reason:
            lines.append(f"- 含糊需求 {requirement.identifier}: {requirement.ambiguity_reason}")
    for item in report.artifacts.main_requirements:
        lines.append(f"- 长期规范 {item.title} @ {item.source_file}:{item.source_line}")
    lines.extend(["", "## 规范对照", ""])
    contrast_limits = [
        item
        for item in report.metadata.limitations
        if item in {"规范对照不可用", "未做 OpenSpec 当前规范对照"}
    ]
    if contrast_limits:
        lines.append(contrast_limits[0])
    elif not report.consistency_items:
        lines.append("没有发现未声明冲突。")
    for item in report.consistency_items:
        lines.append(
            f"- {item.status} {item.summary} @ {item.current_file}:{item.current_line} / {item.change_file}:{item.change_line}"
        )
    lines.extend(["", "## 潜在风险", ""])
    if report.summary.highest_risks:
        for item in report.summary.highest_risks:
            finding = next(found for found in report.findings if found.finding_id == item)
            place = "位置不可用" if finding.location is None else (
                f"{finding.location.file}:{finding.location.line_start}"
            )
            path = finding.failure_path or "失败路径不可用"
            lines.append(
                f"- {finding.finding_id} {finding.summary} ({place}, {finding.evidence_status}, {path})"
            )
    else:
        lines.append("没有形成风险条目。")
    if report.metadata.risk_dispositions:
        for item in report.metadata.risk_dispositions:
            lines.append(f"- 风险类别 {item.risk_class}: {item.disposition}")
        lines.append("这些类别已检查。未发现问题不等于代码安全。")
    lines.extend(["", "## 证据定位", ""])
    if not report.findings and not report.requirements:
        lines.append("当前没有可定位的需求或发现。")
    for finding in report.findings:
        if finding.location is None:
            place = "位置不可用"
        else:
            place = f"{finding.location.file}:{finding.location.line_start}"
        lines.append(f"- {finding.finding_id}: 来源 {finding.origin} @ {place}")
    for requirement in report.requirements:
        evidence = requirement.evidence[-1] if requirement.evidence else None
        status = evidence.status if evidence else "insufficient"
        note = f" {evidence.note}" if evidence and evidence.note else ""
        lines.append(
            f"- 需求 {requirement.identifier}: {status}{note} @ {requirement.source_file}:{requirement.source_line}"
        )
    lines.extend(["", "## 检查结果", ""])
    if not report.checks:
        lines.append("实际执行的检查：无")
    for check in report.checks:
        diagnostic = check.diagnostic if check.diagnostic else "诊断不可用"
        lines.append(
            f"- {check.check_id}: {check.status.value} command={check.command} duration={check.duration_seconds} exit={check.exit_code} diagnostic={diagnostic}"
        )
    modules = ", ".join(report.metadata.modules) if report.metadata.modules else "无"
    lines.append(f"识别到的构建模块: {modules}")
    if report.metadata.module_coverage.not_separately_covered:
        lines.append(
            "仓库级命令没有分别覆盖: " + ", ".join(report.metadata.module_coverage.not_separately_covered)
        )
    if report.summary.reliable_checks:
        lines.append("")
        lines.append("已有可靠证据、不必反复人工确认的检查: " + ", ".join(report.summary.reliable_checks))
    lines.extend(["", "## 限制说明", "", DISCLAIMER, ""])
    calibration = report.metadata.calibration
    if calibration.status == "complete":
        lines.append(f"历史对照已完成，已对照变更数量: {calibration.completed_review_count}")
    else:
        lines.append("历史对照未完成")
    if calibration.rejected_complete_mark:
        lines.append("完成标记已拒绝")
    for note in calibration.notes:
        if note not in {"历史对照未完成", "完成标记已拒绝"}:
            lines.append(f"- {note}")
    if report.summary.coverage_percent is None:
        lines.append("覆盖率分析不可用。")
    else:
        lines.append(f"覆盖率: {report.summary.coverage_percent}")
    for item in report.metadata.limitations:
        lines.append(f"- {item}")
    if report.metadata.service_id or report.metadata.model_id:
        lines.append(
            f"辅助审查服务: {report.metadata.service_id or ''} 模型: {report.metadata.model_id or ''}".rstrip()
        )
    for note in report.metadata.redactions:
        lines.append(f"密钥遮盖 {note.category}: {note.count}")
    if report.metadata.source_snippets:
        lines.append("源码片段:")
        for snippet in report.metadata.source_snippets:
            lines.append(f"- {snippet}")
    if not report.findings:
        names = ", ".join(item.check_id for item in report.checks) or "无"
        lines.append(f"本次没有发现并不表示代码没有缺陷。实际执行的检查：{names}")
    if report.review_status == ReviewStatus.REVIEW_INCOMPLETE:
        lines.append("本次审核不完整，不能当成全部检查已通过。")
    return "\n".join(lines) + "\n"
