import pytest
from pydantic import ValidationError

from specguard.config.models import SpecGuardConfig


def _config(**overrides: object) -> dict:
    data: dict = {
        "version": 1,
        "git": {"base": "main"},
        "llm": {"enabled": False, "external_fallback": False},
        "review": {"llm_findings_block": False},
    }
    data.update(overrides)
    return data


def test_requirements_source_defaults_to_auto() -> None:
    config = SpecGuardConfig.model_validate(_config())
    assert config.requirements.source == "auto"
    assert config.speckit.root == "specs"
    assert config.speckit.feature is None


@pytest.mark.parametrize("source", ["auto", "openspec", "speckit"])
def test_requirements_source_accepts_known_values(source: str) -> None:
    config = SpecGuardConfig.model_validate(_config(requirements={"source": source}))
    assert config.requirements.source == source


def test_speckit_feature_keeps_the_directory_name() -> None:
    config = SpecGuardConfig.model_validate(_config(speckit={"feature": "001-sample"}))
    assert config.speckit.feature == "001-sample"


def test_unknown_requirements_source_is_invalid() -> None:
    with pytest.raises(ValidationError):
        SpecGuardConfig.model_validate(_config(requirements={"source": "git"}))


def test_unknown_config_field_is_still_rejected() -> None:
    with pytest.raises(ValidationError):
        SpecGuardConfig.model_validate(_config(not_a_field=True))
