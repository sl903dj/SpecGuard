import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from specguard import __version__
from specguard.artifacts.provider import load_bundle
from specguard.checks.isolate import isolated_root
from specguard.checks.java import run_java_checks
from specguard.checks.optional_tools import run_optional_checks
from specguard.checks.test_results import note_missing_results, parse_test_result_file
from specguard.config.models import SpecGuardConfig
from specguard.git.diff import collect_changes
from specguard.git.repository import discover_root, read_head, resolve_revision, worktree_dirty
from specguard.llm.client import LlmClient
from specguard.models.entities import (
    DISCLAIMER,
    ArtifactContextEntry,
    ArtifactReport,
    CheckResult,
    Finding,
    Metadata,
    RedactionNote,
    PolicyView,
    ReviewReport,
    Summary,
)
from specguard.models.status import CheckStatus, ReviewStatus
from specguard.report.json_report import render_json
from specguard.report.markdown import render_markdown
from specguard.report.paths import resolve_report_dir
from specguard.report.snippets import limited_snippets
from specguard.review.assisted import (
    build_context,
    error_dimensions,
    merge_llm_output,
    review_messages,
    review_untrusted,
    skipped_dimensions,
)
from specguard.review.policy import decide
from specguard.review.ranking import assign_ids, conflicts_for, highest_risks, reliable_checks
from specguard.llm.redact import merge_redactions, redact
from specguard.review.risk import existing_test_failure_note, missing_logic_context, review_risks
from specguard.review.test_adequacy import assess_tests
from specguard.review.traceability import link_requirements, link_tasks
from specguard.project.detect import detect_project
from specguard.errors import ProviderError, UsageError


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _reader(repo: Path):
    def read_text(path: str) -> str:
        file = repo / path
        if not file.is_file():
            return ""
        return file.read_text(encoding="utf-8", errors="replace")

    return read_text


def findings_from_checks(checks: list[CheckResult]) -> list[Finding]:
    findings: list[Finding] = []
    for check in checks:
        if check.status != CheckStatus.FAIL:
            continue
        category = "test_adequacy" if check.check_id == "tests" else "regression"
        findings.append(
            Finding(
                category=category,  # type: ignore[arg-type]
                severity="high" if check.required else "medium",
                summary=f"确定性检查 {check.check_id} 失败",
                failure_path="已配置的命令返回非零状态。",
                evidence_status="confirmed",
                origin=check.check_id,
            )
        )
    return findings


def _counts(requirements, tasks) -> tuple[int, int, int, int]:
    direct = inferred = insufficient = 0
    for requirement in requirements:
        status = requirement.evidence[-1].status if requirement.evidence else "insufficient"
        if status == "direct":
            direct += 1
        elif status == "inferred":
            inferred += 1
        else:
            insufficient += 1
    gaps = sum(1 for task in tasks if task.marked_complete and task.support == "none")
    return direct, inferred, insufficient, gaps


def _planned_paths(report: ReviewReport, directory: Path, formats: list[str]) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    change = report.metadata.subject_id or report.metadata.change or "no-subject"
    sha = (report.metadata.head_sha or "unknown")[:12]
    stem = f"{change}-{sha}"
    planned: list[str] = []
    if "markdown" in formats:
        planned.append(str(_unique(directory / f"{stem}.md")))
    if "json" in formats:
        planned.append(str(_unique(directory / f"{stem}.json")))
    return planned


def _write_exact(report: ReviewReport, formats: list[str]) -> None:
    for path_text in report.metadata.output_paths:
        path = Path(path_text)
        if path.suffix == ".md" and "markdown" in formats:
            path.write_text(render_markdown(report), encoding="utf-8")
        elif path.suffix == ".json" and "json" in formats:
            path.write_text(json.dumps(render_json(report), ensure_ascii=False, indent=2), encoding="utf-8")


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def run_review(
    config: SpecGuardConfig,
    config_path: Path,
    repo: Path | None = None,
    *,
    cli_subject: str | None = None,
) -> tuple[ReviewReport, int]:
    started = _now()
    root = discover_root(repo or (config_path.parent / config.project.root))
    provider_config = config.artifact_provider_config()
    include_main = config.openspec.include_main_specs
    bundle = load_bundle(
        root,
        provider_config,
        cli_subject,
        include_main_specs=include_main,
        require_selection=config.openspec.require_change_selection,
    )
    base = resolve_revision(root, config.git.base)
    target = resolve_revision(root, config.git.target)
    if config.git.fail_on_uncommitted_changes and not config.git.include_worktree and worktree_dirty(root):
        raise UsageError("工作区有未提交改动。未明确纳入时停止审核。")
    start_head = read_head(root)
    report_dir = resolve_report_dir(root, config.report.output_dir)
    changed = collect_changes(root, base, target, config.git.include_worktree)
    limitations: list[str] = []
    if bundle is None:
        selected = None
        artifact_provider = (
            provider_config.provider if provider_config.provider != "auto" else None
        )
        selection_source = None
        artifacts = ArtifactReport(
            available=False,
            provider=artifact_provider,
            selected_change=None,
        )
        requirements, tasks = [], []
        limitations.append("基于需求的审核不可用")
    else:
        selected = bundle.subject.subject_id
        artifact_provider = bundle.subject.provider
        selection_source = bundle.subject.selection_source
        artifacts = ArtifactReport(
            available=True,
            provider=artifact_provider,
            subject_id=selected,
            selection_source=selection_source,
            found=bundle.found,
            missing=bundle.missing,
            context_documents=[
                ArtifactContextEntry(kind=item.kind, path=item.path)
                for item in bundle.context_documents
            ],
            selected_change=selected,
            main_specs=bundle.main_specs,
            main_requirements=bundle.main_requirements,
        )
        requirements, tasks = bundle.requirements, bundle.tasks
        limitations.extend(bundle.limitations)
    read_text = _reader(root)
    findings: list[Finding] = []
    findings.extend(link_requirements(requirements, changed, read_text))
    findings.extend(link_tasks(tasks, changed, read_text))
    layout = detect_project(root)
    if layout.limitation:
        limitations.append(layout.limitation)
    workdir = root
    if not config.security.isolate_builds:
        checks = [
            CheckResult(
                check_id=name,
                required=getattr(config.checks, name).required,
                status=CheckStatus.ERROR if getattr(config.checks, name).required else CheckStatus.SKIPPED,
                command=getattr(config.checks, name).command,
                diagnostic="隔离已关闭，拒绝在被审核仓库执行项目命令",
            )
            for name in (
                "build",
                "tests",
                "checkstyle",
                "spotbugs",
                "pmd",
                "jacoco",
                "archunit",
                "openspec_validate",
            )
            if getattr(config.checks, name).enabled
        ]
    elif config.security.isolate_builds:
        workdir, isolate_error = isolated_root(root, True)
        if isolate_error or workdir is None:
            limitations.append(f"构建隔离失败: {isolate_error}")
            checks = [
                CheckResult(
                    check_id=name,
                    required=getattr(config.checks, name).required,
                    status=CheckStatus.ERROR,
                    diagnostic="隔离工作区失败，未在原仓库执行构建",
                )
                for name in ("build", "tests")
                if getattr(config.checks, name).enabled
            ]
        else:
            checks = run_java_checks(config.checks, workdir, config.security.max_command_output_bytes)
            checks.extend(run_optional_checks(config.checks, workdir, config.security.max_command_output_bytes))
    findings.extend(findings_from_checks(checks))
    test_check = next((item for item in checks if item.check_id == "tests"), None)
    if test_check is not None:
        note = existing_test_failure_note(test_check, {item.path for item in changed})
        if note is not None:
            findings.append(note)
        if parse_test_result_file(None) is None:
            missing = note_missing_results(test_check if test_check.status != CheckStatus.PASS else None)
            if missing and test_check.status != CheckStatus.PASS:
                findings.append(missing)
    findings.extend(review_risks(changed, read_text))
    limitations.extend(missing_logic_context(changed, read_text))
    if config.checks.build.enabled or config.checks.tests.enabled:
        limitations.append("构建和测试命令可能生成文件，并执行项目自带脚本。")
    coverage_available = any(item.check_id == "jacoco" and item.status == CheckStatus.PASS for item in checks)
    extra, _ignored_coverage = assess_tests(requirements, changed, read_text, test_check, coverage_available)
    findings.extend(extra)
    parsed_results = parse_test_result_file(test_check.diagnostic if test_check and test_check.diagnostic else None)
    coverage = parsed_results.get("coverage_percent") if parsed_results else None
    if coverage is None:
        limitations.append("覆盖率分析不可用")
    service_id = None
    model_id = None
    redaction_notes: list[dict] = []
    if config.review.mode == "assisted":
        untrusted_source = "\n".join(read_text(item.path) for item in changed)
        kept_policy = review_untrusted(untrusted_source, config.review)
        if kept_policy.policy != config.review.policy or kept_policy.llm_findings_block:
            raise UsageError("不可信内容试图改写审核策略")
        service_id = urlparse(config.llm.base_url or "").netloc or None
        model_id = config.llm.model
        context, truncated, redaction_notes = build_context(
            changed,
            read_text,
            config.llm.max_context_chars,
            context_documents=bundle.context_documents if bundle is not None else [],
        )
        main_blob = "\n".join(f"{item.title}\n{item.body}" for item in artifacts.main_requirements)
        if main_blob:
            cleaned_main, main_notes = redact(main_blob)
            redaction_notes = merge_redactions([*redaction_notes, *main_notes])
            context = f"{cleaned_main}\n{context}"
            if len(context) > config.llm.max_context_chars:
                context = context[: config.llm.max_context_chars]
                truncated = True
        if truncated:
            limitations.append("辅助审查上下文已按上限截断")
        try:
            client = LlmClient(config.llm)
            payload = client.post_review({"messages": review_messages(context)})
            findings.extend(merge_llm_output(payload, {item.path for item in changed}))
            checks.extend(
                [
                    CheckResult(check_id=name, required=False, status=CheckStatus.PASS, diagnostic="辅助审查已返回")
                    for name in (
                        "assisted_requirements",
                        "assisted_business_logic",
                        "assisted_test_adequacy",
                        "assisted_regression",
                    )
                ]
            )
        except ProviderError as exc:
            checks.extend(error_dimensions(str(exc)))
            limitations.append(str(exc))
    else:
        checks.extend(skipped_dimensions())
    findings = assign_ids(findings)
    conflicts = conflicts_for(findings)
    direct, inferred, insufficient, gaps = _counts(requirements, tasks)
    needs_human = bool(insufficient or gaps or conflicts or any(item.ambiguous for item in requirements) or any(
        item.evidence_status in {"hypothesis", "insufficient"} for item in findings
    ))
    end_head = read_head(root)
    status, blocked, reasons = decide(config.review, findings, checks)
    if end_head != start_head:
        status = ReviewStatus.REVIEW_INCOMPLETE
        blocked = False
        limitations.append("审核期间版本库状态发生变化，报告不完整")
    summary = Summary(
        needs_human_review=needs_human or status != ReviewStatus.REVIEW_COMPLETE,
        direct_count=direct,
        inferred_count=inferred,
        insufficient_count=insufficient,
        task_gap_count=gaps,
        highest_risks=highest_risks(findings),
        reliable_checks=reliable_checks(checks),
        disclaimer=DISCLAIMER,
        coverage_percent=coverage,
    )
    report = ReviewReport(
        review_status=status,
        policy=PolicyView(mode=config.review.policy, blocked=blocked, reasons=reasons),
        metadata=Metadata(
            tool_version=__version__,
            config_version=config.version,
            repository_root=str(root),
            base=base,
            target=target,
            head_sha=start_head,
            change=selected,
            artifact_provider=artifact_provider,
            subject_id=selected,
            selection_source=selection_source,
            started_at=started,
            finished_at=_now(),
            limitations=limitations,
            modules=layout.modules,
            redactions=[RedactionNote(category=item["category"], count=item["count"]) for item in redaction_notes],
            service_id=service_id,
            model_id=model_id,
            source_snippets=limited_snippets(changed, read_text, config.report.include_source_snippets),
        ),
        summary=summary,
        changed_files=changed,
        requirements=requirements,
        tasks=tasks,
        checks=checks,
        findings=findings,
        conflicts=conflicts,
        artifacts=artifacts,
    )
    report.metadata.output_paths = _planned_paths(report, report_dir, list(config.report.formats))
    _write_exact(report, list(config.report.formats))
    from specguard.cli.exit_codes import exit_for

    return report, exit_for(report.review_status)
