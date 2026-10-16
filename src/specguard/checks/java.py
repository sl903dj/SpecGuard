from pathlib import Path

from specguard.checks.runner import run_configured_check
from specguard.config.models import CheckSpec, ChecksConfig
from specguard.models.entities import CheckResult


def command_for(spec: CheckSpec) -> str | None:
    return spec.command


def run_java_checks(
    checks: ChecksConfig,
    cwd: Path,
    max_bytes: int,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name in ("build", "tests"):
        spec = getattr(checks, name)
        result = run_configured_check(
            name,
            command_for(spec),
            spec.enabled,
            spec.required,
            spec.timeout_seconds,
            max_bytes,
            cwd,
        )
        if result is not None:
            results.append(result)
    return results
