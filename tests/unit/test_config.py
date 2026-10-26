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


@pytest.mark.parametrize("provider", ["openspec", "speckit", "auto"])
def test_artifact_provider_values_and_defaults(tmp_path: Path, provider: str) -> None:
    data = _base()
    data["artifacts"] = {"provider": provider}
    loaded = load_config(_write(tmp_path, data))
    assert loaded.artifacts is not None
    assert loaded.artifacts.provider == provider
    assert loaded.artifacts.include_context is True


def test_report_requires_both_formats(tmp_path: Path) -> None:
    data = _base()
    data["report"] = {"formats": ["json"]}
    with pytest.raises(ConfigError, match="markdown"):
        load_config(_write(tmp_path, data))


def test_public_model_url_rejected_when_external_network_disabled(tmp_path: Path) -> None:
    data = _base()
    data["review"]["mode"] = "assisted"
    data["llm"].update({"enabled": True, "base_url": "https://api.openai.com/v1"})
    data["security"] = {"external_network": False}
    with pytest.raises(ConfigError, match="内网"):
        load_config(_write(tmp_path, data))
    data["llm"]["base_url"] = "http://10.1.2.3/v1"
    assert load_config(_write(tmp_path, data)).llm.base_url == "http://10.1.2.3/v1"
    data["llm"]["base_url"] = "http://127.0.0.1:9/v1"
    assert load_config(_write(tmp_path, data)).llm.base_url.endswith("/v1")


def test_artifact_root_must_be_repository_relative(tmp_path: Path) -> None:
    data = _base()
    data["artifacts"] = {"provider": "speckit", "root": "../specs"}
    with pytest.raises(ConfigError, match="相对路径"):
        load_config(_write(tmp_path, data))


def test_matching_dual_config_is_accepted_and_conflicts_rejected(tmp_path: Path) -> None:
    data = _base()
    data["openspec"] = {"root": "openspec", "change": "one"}
    data["artifacts"] = {
        "provider": "openspec",
        "root": "openspec",
        "subject": "one",
    }
    assert load_config(_write(tmp_path, data)).artifact_provider_config().subject == "one"
    data["artifacts"]["provider"] = "speckit"
    with pytest.raises(ConfigError, match="冲突"):
        load_config(_write(tmp_path, data))
