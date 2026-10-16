from pathlib import Path

from specguard.checks.runner import execute, run_configured_check
from specguard.models.status import CheckStatus


def test_success_records_command_duration_and_exit(tmp_path: Path) -> None:
    status, code, duration, _diagnostic = execute(["python3", "-c", "print('ok')"], tmp_path, 5, 100)
    assert status == CheckStatus.PASS
    assert code == 0
    assert duration >= 0


def test_failure_keeps_bounded_diagnostic(tmp_path: Path) -> None:
    status, code, _duration, diagnostic = execute(
        ["python3", "-c", "import sys; sys.stderr.write('x' * 500); raise SystemExit(2)"],
        tmp_path,
        5,
        40,
    )
    assert status == CheckStatus.FAIL
    assert code == 2
    assert len(diagnostic) <= 40


def test_timeout_kills_the_process(tmp_path: Path) -> None:
    status, _code, _duration, diagnostic = execute(["sleep", "5"], tmp_path, 0.2, 100)
    assert status == CheckStatus.TIMEOUT
    assert "超时" in diagnostic


def test_missing_tool_is_not_pass(tmp_path: Path) -> None:
    optional = run_configured_check("checkstyle", "./mvnw-missing -q", True, False, 5, 100, tmp_path)
    required = run_configured_check("build", "./mvnw-missing -q", True, True, 5, 100, tmp_path)
    assert optional is not None and optional.status == CheckStatus.SKIPPED
    assert required is not None and required.status == CheckStatus.ERROR
    assert optional.status != CheckStatus.PASS
    assert required.status != CheckStatus.PASS
