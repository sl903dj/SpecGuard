from pathlib import Path

import pytest
import yaml

from specguard.config.loader import load_config
from specguard.errors import ConfigError


def _base() -> dict:
    return {
        "version": 1,
        "git": {"base": "main"},
        "review": {"mode": "static", "policy": "advisory", "llm_findings_block": False},
        "llm": {"enabled": False, "external_fallback": False},
        "checks": {"build": {"enabled": True, "required": True, "command": "./mvnw -q test"}},
    }


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "specguard.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_valid_config_loads(tmp_path: Path) -> None:
    loaded = load_config(_write(tmp_path, _base()))
    assert loaded.version == 1
    assert loaded.review.llm_findings_block is False


def test_version_must_be_one(tmp_path: Path) -> None:
    data = _base()
    data["version"] = 2
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, data))
    assert "version" in str(exc.value)


def test_llm_findings_cannot_block(tmp_path: Path) -> None:
    data = _base()
    data["review"]["llm_findings_block"] = True
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, data))
    assert "llm_findings_block" in str(exc.value)


def test_external_fallback_rejected(tmp_path: Path) -> None:
    data = _base()
    data["llm"]["external_fallback"] = True
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, data))
    assert "external_fallback" in str(exc.value)


def test_unknown_field_rejected(tmp_path: Path) -> None:
    data = _base()
    data["review"]["surprise"] = True
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, data))
    assert "surprise" in str(exc.value)


def test_command_outside_allowlist_rejected(tmp_path: Path) -> None:
    data = _base()
    data["checks"]["build"]["command"] = "curl http://evil.example"
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, data))
    assert "命令不在允许列表中" in str(exc.value)


def test_assisted_without_base_url_rejected(tmp_path: Path) -> None:
    data = _base()
    data["review"]["mode"] = "assisted"
    data["llm"]["enabled"] = True
    data["llm"]["base_url"] = None
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, data))
    assert "base_url" in str(exc.value)
