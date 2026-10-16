from specguard.models.entities import CheckResult, Finding
from specguard.models.status import CheckStatus

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def assign_ids(findings: list[Finding]) -> list[Finding]:
    ordered = sorted(
        findings,
        key=lambda item: (
            SEVERITY_RANK[item.severity],
            item.location.file if item.location else "",
            item.location.line_start if item.location else 0,
            item.origin,
            item.summary,
        ),
    )
    groups: dict[tuple, list[Finding]] = {}
    for index, finding in enumerate(ordered, start=1):
        finding.finding_id = f"SG-{finding.category}-{index}"
        if finding.location is None:
            continue
        key = (finding.category, finding.location.file, finding.location.line_start, finding.summary)
        groups.setdefault(key, []).append(finding)
    group_no = 1
    for bucket in groups.values():
        if len(bucket) < 2:
            continue
        label = f"dup-{group_no}"
        group_no += 1
        for finding in bucket:
            finding.duplicate_group = label
    return ordered


def conflicts_for(findings: list[Finding]) -> list[list[str]]:
    buckets: dict[tuple, list[Finding]] = {}
    for finding in findings:
        if finding.location is None:
            continue
        key = (finding.location.file, finding.location.line_start)
        buckets.setdefault(key, []).append(finding)
    conflicts: list[list[str]] = []
    for bucket in buckets.values():
        summaries = {item.summary for item in bucket}
        if len(summaries) > 1:
            conflicts.append([item.finding_id for item in bucket])
    return conflicts


def highest_risks(findings: list[Finding], limit: int = 10) -> list[str]:
    return [item.finding_id for item in findings[:limit]]


def reliable_checks(checks: list[CheckResult]) -> list[str]:
    return [
        item.check_id
        for item in checks
        if item.status in {CheckStatus.PASS, CheckStatus.FAIL}
        and not item.check_id.startswith("assisted")
    ]
