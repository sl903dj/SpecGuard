from pathlib import Path

import yaml

from specguard.config.models import SpecGuardConfig

ROOT = Path(__file__).resolve().parents[2]


def test_three_config_templates_validate() -> None:
    text = (ROOT / "docs" / "config-templates.md").read_text(encoding="utf-8")
    blocks = [part.split("```", 1)[0] for part in text.split("```yaml")[1:]]
    assert len(blocks) == 3
    loaded = [yaml.safe_load(block) for block in blocks]
    for raw, data in zip(blocks, loaded, strict=True):
        config = SpecGuardConfig.model_validate(data)
        assert config.review.mode == "static"
        assert config.review.policy == "advisory"
        assert config.review.llm_findings_block is False
        assert config.llm.external_fallback is False
        assert "llm.base_url" not in raw

    assert "checks" not in loaded[0]
    standard = loaded[1]
    assert standard["checks"]["build"]["command"] == "./mvnw -q -DskipTests package"
    assert standard["checks"]["build"]["enabled"] is True
    assert standard["checks"]["build"]["required"] is True
    assert standard["checks"]["tests"]["command"] == "./mvnw -q test"
    assert standard["checks"]["tests"]["enabled"] is True
    assert standard["checks"]["tests"]["required"] is True

    recommended = loaded[2]
    assert recommended["checks"]["build"]["command"] == "./mvnw -q -DskipTests package"
    assert recommended["checks"]["tests"]["command"] == "./mvnw -q test"
    for name, command in (
        ("checkstyle", "checkstyle"),
        ("spotbugs", "spotbugs"),
        ("pmd", "pmd"),
    ):
        item = recommended["checks"][name]
        assert item["enabled"] is True
        assert item["required"] is False
        assert item["command"] == command

    assert "specguard.yaml" in text
    assert "仓库根" in text
    assert "不自动加载" in text
    assert "./gradlew assemble" in text
    assert "./gradlew test" in text

    usage = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")
    section = usage.split("## 4. 编写最小配置", 1)[1].split("## 5.", 1)[0]
    assert "docs/config-templates.md" in section
