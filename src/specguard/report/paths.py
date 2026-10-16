from pathlib import Path

from specguard.errors import UsageError

SOURCE_SUFFIXES = {".java", ".py", ".kt", ".md", ".xml", ".gradle", ".kts"}


def resolve_report_dir(repo_root: Path, output_dir: str) -> Path:
    root = repo_root.resolve()
    allowed = (root / ".specguard" / "reports").resolve()
    raw = Path(output_dir)
    candidate = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    if ".." in Path(output_dir).parts:
        raise UsageError(f"报告路径非法: {output_dir}")
    if ".git" in candidate.parts:
        raise UsageError(f"报告路径指向 Git 元数据: {output_dir}")
    try:
        candidate.relative_to(allowed)
    except ValueError as exc:
        raise UsageError(f"报告路径必须位于 {allowed}: {output_dir}") from exc
    if candidate.suffix in SOURCE_SUFFIXES:
        raise UsageError(f"报告路径不能覆盖源文件: {output_dir}")
    return candidate
