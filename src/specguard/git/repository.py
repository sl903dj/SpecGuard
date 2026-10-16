import subprocess
from pathlib import Path

from specguard.errors import ReadOnlyError, UsageError

MUTATING = {
    "add",
    "commit",
    "checkout",
    "switch",
    "reset",
    "merge",
    "clean",
    "rebase",
    "cherry-pick",
    "revert",
    "stash",
    "push",
    "pull",
    "fetch",
    "init",
    "branch",
    "tag",
    "mv",
    "rm",
    "restore",
    "update-index",
}


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    if not args or args[0] in MUTATING:
        raise ReadOnlyError(f"拒绝修改版本库的 Git 命令: {args[0] if args else ''}")
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def discover_root(start: Path) -> Path:
    result = run_git(["rev-parse", "--show-toplevel"], start)
    if result.returncode != 0:
        raise UsageError("当前目录不在版本库中。请在 Git 仓库内运行审核。")
    return Path(result.stdout.strip())


def resolve_revision(repo: Path, revision: str) -> str:
    result = run_git(["rev-parse", "--verify", "--end-of-options", revision], repo)
    if result.returncode != 0:
        raise UsageError(f"无法解析版本 {revision}")
    return result.stdout.strip()


def read_head(repo: Path) -> str:
    return resolve_revision(repo, "HEAD")


def worktree_dirty(repo: Path) -> bool:
    result = run_git(["status", "--porcelain"], repo)
    if result.returncode != 0:
        raise UsageError("无法读取工作区状态")
    for line in result.stdout.splitlines():
        path = line[3:].strip().strip('"')
        if path.startswith(".specguard/") or path == ".specguard":
            continue
        return True
    return False
