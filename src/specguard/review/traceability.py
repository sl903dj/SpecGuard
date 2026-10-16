from specguard.models.entities import (
    ChangedFile,
    Evidence,
    Finding,
    Requirement,
    TaskItem,
)


def _is_test_path(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    return "/test/" in lowered or lowered.endswith("test.java") or "/tests/" in lowered


def _read(read_text, path: str) -> str:
    if read_text is None:
        return ""
    return read_text(path) or ""


def link_requirements(
    requirements: list[Requirement],
    changed_files: list[ChangedFile],
    read_text=None,
) -> list[Finding]:
    findings: list[Finding] = []
    linked_paths: set[str] = set()
    for requirement in requirements:
        if requirement.change_semantics == "removed":
            requirement.evidence.append(
                Evidence(
                    status="insufficient",
                    requirement_id=requirement.identifier,
                    note="需求被删除，不把删除本身记成缺陷",
                )
            )
            continue
        direct = []
        inferred = []
        for changed in changed_files:
            name = changed.path.rsplit("/", 1)[-1]
            content = _read(read_text, changed.path)
            if requirement.identifier in content:
                direct.append(changed.path)
            elif name and (name in requirement.body or name in requirement.title):
                inferred.append(changed.path)
        if direct:
            linked_paths.update(direct)
            requirement.evidence.append(
                Evidence(
                    status="direct",
                    requirement_id=requirement.identifier,
                    file=direct[0],
                    note="变更文件包含需求标识",
                )
            )
        elif inferred:
            linked_paths.update(inferred)
            requirement.evidence.append(
                Evidence(
                    status="inferred",
                    requirement_id=requirement.identifier,
                    file=inferred[0],
                    note="仅有文件名重叠，不能单独证明需求已实现",
                )
            )
        else:
            requirement.evidence.append(
                Evidence(
                    status="insufficient",
                    requirement_id=requirement.identifier,
                    note="找不到实现证据",
                )
            )
    for changed in changed_files:
        if _is_test_path(changed.path) or changed.path in linked_paths:
            continue
        if changed.change_type == "deleted":
            continue
        findings.append(
            Finding(
                category="requirements",
                severity="medium",
                summary=f"{changed.path} 无法追溯到需求，可能是擅自扩展，需要人工审核",
                evidence_status="insufficient",
                origin="traceability",
                location=None,
            )
        )
    return findings


def link_tasks(
    tasks: list[TaskItem],
    changed_files: list[ChangedFile],
    read_text=None,
) -> list[Finding]:
    findings: list[Finding] = []
    for task in tasks:
        has_code = False
        has_test = False
        for changed in changed_files:
            content = _read(read_text, changed.path)
            haystack = content + " " + changed.path
            if task.identifier not in haystack and task.text not in haystack:
                continue
            if _is_test_path(changed.path):
                has_test = True
            else:
                has_code = True
        if has_code and has_test:
            task.support = "both"
        elif has_test:
            task.support = "test"
        elif has_code:
            task.support = "code"
        else:
            task.support = "none"
        if task.marked_complete and task.support == "none":
            task.evidence.append(
                Evidence(
                    status="insufficient",
                    task_id=task.identifier,
                    note="任务已勾选完成，但没有代码或测试支撑",
                )
            )
            findings.append(
                Finding(
                    category="task_integrity",
                    severity="medium",
                    summary=f"任务 {task.identifier} 已标为完成，但缺少代码或测试支撑",
                    evidence_status="insufficient",
                    origin="traceability",
                    related_task_ids=[task.identifier],
                )
            )
        elif task.support != "none":
            task.evidence.append(
                Evidence(
                    status="inferred",
                    task_id=task.identifier,
                    note="任务文本或标识出现在变更文件中",
                )
            )
    return findings
