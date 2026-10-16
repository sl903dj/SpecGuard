from pathlib import Path

from specguard.checks.runner import run_configured_check
from specguard.config.models import ChecksConfig
from specguard.models.entities import CheckResult

OPTIONAL = ("checkstyle", "spotbugs", "pmd", "jacoco", "archunit", "openspec_validate")


def run_optional_checks(checks: ChecksConfig, cwd: Path, max_bytes: int) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name in OPTIONAL:
        spec = getattr(checks, name)
        result = run_configured_check(
            name,
            spec.command,
            spec.enabled,
            spec.required,
            spec.timeout_seconds,
            max_bytes,
            cwd,
        )
        if result is not None:
            results.append(result)
    return results
