import json
import re
from pathlib import Path

from specguard.errors import UsageError

FEATURE_NAME = re.compile(r"^[0-9]+-.+")


def list_features(repo: Path, specs_root: str = "specs") -> list[str]:
    root = repo / specs_root
    if not root.is_dir():
        return []
    names: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or not FEATURE_NAME.match(child.name):
            continue
        if (child / "spec.md").is_file():
            names.append(child.name)
    return names


def feature_json_hint(repo: Path) -> str | None:
    path = repo / ".specify" / "feature.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("feature_directory")
    if isinstance(value, str) and value.strip():
        return value
    return None


def select_feature(names: list[str], requested: str | None, hint: str | None) -> str | None:
    if requested:
        if requested not in names:
            raise UsageError(f"无法找到 Spec Kit 功能 {requested}")
        return requested
    if len(names) == 1:
        return names[0]
    if len(names) > 1:
        message = "存在多个 Spec Kit 功能，请明确选择: " + ", ".join(names)
        if hint:
            message += f"。feature.json 指向 {hint}"
        raise UsageError(message)
    return None
