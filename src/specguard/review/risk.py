import re
from pathlib import Path

from specguard.models.entities import (
    ChangedFile,
    CheckResult,
    Finding,
    Location,
    RiskClass,
    RiskDisposition,
)
from specguard.models.status import CheckStatus

RISK_CLASSES: tuple[RiskClass, ...] = (
    "boundary",
    "exception",
    "null_empty",
    "transaction",
    "concurrency",
    "authorization",
    "compatibility",
    "persisted_data",
    "dependency_config",
)

EMPTY_CATCH = re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}")
BOUNDARY = re.compile(r"<=\s*[\w.]+\.(?:size|length)\(\)")
PUBLIC_METHOD = re.compile(r"^\s*public\s+[\w<>\[\], ?]+\s+(\w+)\s*\(")
EMPTY_NULL = re.compile(r"if\s*\([^)]*==\s*null\s*\)\s*\{\s*\}")
CONTEXT_MARKERS = (
    "== null",
    "setStatus",
    "@Transactional",
    "synchronized",
    "PreAuthorize",
    "HashMap",
    "ConcurrentHashMap",
    "@GetMapping",
    "@PostMapping",
    "@PutMapping",
    "@DeleteMapping",
    "@RequestMapping",
    "RolesAllowed",
)


def _location(path: str, start: int | None, end: int | None) -> Location | None:
    if start is None or start <= 0:
        return None
    return Location(file=path, line_start=start, line_end=end or start)


def _line_of(text: str, needle: str) -> int | None:
    index = text.find(needle)
    if index < 0:
        return None
    return text.count("\n", 0, index) + 1


def _insufficient(
    category: str,
    summary: str,
    path: str,
    line: int | None,
    *,
    failure_path: str | None = None,
    risk_class: RiskClass | None = None,
) -> Finding:
    return Finding(
        category=category,  # type: ignore[arg-type]
        severity="medium",
        summary=summary,
        evidence_status="insufficient",
        origin="risk",
        risk_class=risk_class,
        location=_location(path, line, line),
        failure_path=failure_path,
    )


def _path_risks(changed: ChangedFile, text: str) -> list[Finding]:
    name = changed.path.replace("\\", "/").rsplit("/", 1)[-1]
    findings: list[Finding] = []
    if name == "pom.xml" or name.startswith("build.gradle"):
        findings.append(
            _insufficient(
                "regression",
                "依赖或构建配置发生变化。这是假设，不是已核实的不兼容。",
                changed.path,
                None,
            )
        )
    if name.endswith((".yml", ".yaml", ".properties")):
        findings.append(
            _insufficient(
                "regression",
                "应用配置发生变化。这是假设，不是已核实的不兼容。",
                changed.path,
                None,
            )
        )
    if name.endswith(".sql") or "@Entity" in text or "@Table" in text:
        line = _line_of(text, "@Entity") or _line_of(text, "@Table")
        findings.append(
            _insufficient(
                "regression",
                "数据保存或数据结构发生变化。这是假设，不是已核实的不兼容。",
                changed.path,
                line,
                failure_path="已保存的数据结构发生变化后，旧数据可能无法读取。这是假设，不是已核实的不兼容。"
                if line
                else None,
                risk_class="persisted_data" if line else None,
            )
        )
    return findings


def _context_findings(path: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    mappings = ("@RequestMapping", "@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping")
    if any(token in text for token in mappings) and not any(
        token in text for token in ("PreAuthorize", "RolesAllowed", "SecurityContext")
    ):
        line = next((_line_of(text, token) for token in mappings if token in text), None)
        findings.append(
            _insufficient(
                "business_logic",
                "可见接口映射，但本次变更里看不到授权检查。这不是已核实的授权缺陷。",
                path,
                line,
                failure_path="请求进入映射方法时，看不到授权检查。这是假设，不是已核实的缺陷。",
                risk_class="authorization",
            )
        )
    if re.search(r"\bsave\s*\(", text) and "@Transactional" not in text:
        findings.append(
            _insufficient(
                "business_logic",
                "可见保存操作，但本次变更里看不到事务边界。这不是已核实的事务缺陷。",
                path,
                _line_of(text, "save"),
                failure_path="保存发生时看不到事务边界。这是假设，不是已核实的缺陷。",
                risk_class="transaction",
            )
        )
    if re.search(r"\bHashMap\s*<", text) and "ConcurrentHashMap" not in text and "synchronized" not in text:
        findings.append(
            _insufficient(
                "business_logic",
                "可见共享可变映射，但本次变更里看不到并发控制。这不是已核实的并发缺陷。",
                path,
                _line_of(text, "HashMap"),
                failure_path="共享映射被并发写入时可能丢失更新。这是假设，不是已核实的缺陷。",
                risk_class="concurrency",
            )
        )
    if "setStatus(" in text and not re.search(r"if\s*\(", text):
        findings.append(
            _insufficient(
                "business_logic",
                "看到状态写入，但看不到转移条件。这不是已核实的状态缺陷。",
                path,
                _line_of(text, "setStatus("),
            )
        )
    return findings


def missing_logic_context(changed_files: list[ChangedFile], read_text) -> list[str]:
    blob = "\n".join((read_text(item.path) if read_text else "") for item in changed_files)
    if any(marker in blob for marker in CONTEXT_MARKERS):
        return []
    return [
        "变更里看不到状态流转、空值与空输入、事务边界、并发或授权的足够上下文，未将这些方面标成已确认缺陷。"
    ]


def review_risks(changed_files: list[ChangedFile], read_text) -> list[Finding]:
    findings: list[Finding] = []
    for changed in changed_files:
        text = read_text(changed.path) if read_text else ""
        findings.extend(_path_risks(changed, text))
        findings.extend(_context_findings(changed.path, text))
        lines = text.splitlines()
        ranges = changed.line_ranges or []
        numbers = []
        for item in ranges:
            numbers.extend(range(item.start, item.end + 1))
        if not numbers:
            findings.append(
                Finding(
                    category="business_logic",
                    severity="low",
                    summary=f"{changed.path} 缺少精确行范围，不能据此判定缺陷",
                    evidence_status="insufficient",
                    origin="risk",
                    location=None,
                )
            )
            continue
        for number in numbers:
            if number <= 0 or number > len(lines):
                continue
            line = lines[number - 1]
            if EMPTY_NULL.search(line):
                findings.append(
                    Finding(
                        category="business_logic",
                        severity="high",
                        summary="空的空值判断会忽略空输入",
                        failure_path="空值被忽略后，后续逻辑会按已有数据继续执行。",
                        evidence_status="confirmed",
                        origin="risk",
                        risk_class="null_empty",
                        location=_location(changed.path, number, number),
                    )
                )
            if EMPTY_CATCH.search(line):
                findings.append(
                    Finding(
                        category="business_logic",
                        severity="high",
                        summary="空的 catch 会吞掉异常",
                        failure_path="异常被空 catch 吃掉后，调用方会以为操作已经成功。",
                        evidence_status="confirmed",
                        origin="risk",
                        risk_class="exception",
                        location=_location(changed.path, number, number),
                    )
                )
            if BOUNDARY.search(line):
                findings.append(
                    Finding(
                        category="business_logic",
                        severity="high",
                        summary="边界比较可能在集合长度上越界",
                        failure_path="当索引等于集合大小时，访问会越界。",
                        evidence_status="confirmed",
                        origin="risk",
                        risk_class="boundary",
                        location=_location(changed.path, number, number),
                    )
                )
            method = PUBLIC_METHOD.search(line)
            if method:
                name = method.group(1)
                callers = [
                    other.path
                    for other in changed_files
                    if other.path != changed.path and name and name in (read_text(other.path) if read_text else "")
                ]
                caller_note = (
                    f" 本次变更中可见调用方 {callers[0]}。"
                    if callers
                    else " 本次变更中未找到调用方。"
                )
                findings.append(
                    Finding(
                        category="regression",
                        severity="medium",
                        summary="公开方法签名发生变化，存在潜在的兼容性风险。这是假设，不是已核实的不兼容。"
                        + caller_note,
                        evidence_status="insufficient",
                        origin="risk",
                        risk_class="compatibility",
                        location=_location(changed.path, number, number),
                        failure_path="签名变化后，已有调用方可能无法按原约定调用。这是假设，不是已核实的不兼容。",
                    )
                )
    return findings


def review_risk_report(
    changed_files: list[ChangedFile],
    read_text,
) -> tuple[list[Finding], list[RiskDisposition]]:
    findings = review_risks(changed_files, read_text)
    covered = {
        item.risk_class
        for item in findings
        if item.risk_class and item.location is not None and item.failure_path
    }
    dispositions = [
        RiskDisposition(
            risk_class=name,
            disposition="finding" if name in covered else "missing_context",
        )
        for name in RISK_CLASSES
    ]
    return findings, dispositions


def existing_test_failure_note(check: CheckResult, changed_paths: set[str]) -> Finding | None:
    if check.check_id != "tests" or check.status != CheckStatus.FAIL:
        return None
    mentioned = [path for path in changed_paths if path and path in (check.diagnostic or "")]
    attributed = bool(mentioned)
    summary = "审核期间既有测试失败。"
    if not attributed:
        summary += "没有证据支持把失败算到这次修改上。"
    return Finding(
        category="test_adequacy",
        severity="high",
        summary=summary,
        failure_path="测试命令返回非零状态。" if attributed else None,
        evidence_status="confirmed" if attributed else "insufficient",
        origin="tests",
        attributes_cause=attributed,
    )
