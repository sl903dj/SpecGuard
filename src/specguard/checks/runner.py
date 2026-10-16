import os
import shlex
import signal
import subprocess
import time
from pathlib import Path
from shutil import which

from specguard.models.entities import CheckResult
from specguard.models.status import CheckStatus


def _truncate(text: str, limit: int) -> str:
    return text[:limit]


def execute(
    argv: list[str],
    cwd: Path,
    timeout: float,
    max_bytes: int,
) -> tuple[CheckStatus, int | None, float, str]:
    start = time.monotonic()
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        duration = time.monotonic() - start
        return CheckStatus.TIMEOUT, None, duration, "检查超时，已终止进程"
    duration = time.monotonic() - start
    diagnostic = _truncate((out or "") + (err or ""), max_bytes)
    if proc.returncode == 0:
        return CheckStatus.PASS, proc.returncode, duration, diagnostic
    return CheckStatus.FAIL, proc.returncode, duration, diagnostic


def tool_exists(command: str, cwd: Path) -> bool:
    argv = shlex.split(command)
    if not argv:
        return False
    executable = argv[0]
    candidate = Path(executable)
    if candidate.is_absolute() or executable.startswith("."):
        return (cwd / executable).exists() or candidate.exists()
    return which(executable) is not None


def run_configured_check(
    check_id: str,
    command: str | None,
    enabled: bool,
    required: bool,
    timeout: int,
    max_bytes: int,
    cwd: Path,
) -> CheckResult | None:
    if not enabled:
        return None
    if not command:
        return CheckResult(
            check_id=check_id,
            required=required,
            status=CheckStatus.ERROR if required else CheckStatus.SKIPPED,
            diagnostic="未配置命令，不猜测构建或测试命令",
        )
    if not tool_exists(command, cwd):
        return CheckResult(
            check_id=check_id,
            required=required,
            status=CheckStatus.ERROR if required else CheckStatus.SKIPPED,
            command=command,
            diagnostic="工具不存在",
        )
    status, code, duration, diagnostic = execute(shlex.split(command), cwd, timeout, max_bytes)
    return CheckResult(
        check_id=check_id,
        required=required,
        status=status,
        command=command,
        duration_seconds=duration,
        exit_code=code,
        diagnostic=diagnostic,
    )
