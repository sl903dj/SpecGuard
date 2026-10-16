import shutil
import tempfile
from pathlib import Path


def isolated_root(src: Path, isolate: bool, copytree=shutil.copytree) -> tuple[Path | None, str | None]:
    if not isolate:
        return src, None
    try:
        dest = Path(tempfile.mkdtemp(prefix="specguard-")) / "work"
        copytree(src, dest, symlinks=False)
        return dest, None
    except Exception as exc:  # isolation must surface as a check error, not a pass
        return None, str(exc)
