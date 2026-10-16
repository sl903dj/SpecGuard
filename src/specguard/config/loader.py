from pathlib import Path

import yaml
from pydantic import ValidationError

from specguard.config.models import SpecGuardConfig
from specguard.errors import ConfigError


def load_config(path: Path) -> SpecGuardConfig:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"无法读取配置 {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"配置不是合法的 YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("配置文件的顶层必须是映射")
    try:
        return SpecGuardConfig.model_validate(raw)
    except ValidationError as exc:
        lines = []
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"]) or "<root>"
            lines.append(f"{loc}: {err['msg']}")
        raise ConfigError("配置无效\n" + "\n".join(lines)) from exc


def config_directory(path: Path) -> Path:
    return path.resolve().parent
