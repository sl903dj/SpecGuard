from pathlib import Path

from specguard.checks.java import command_for
from specguard.checks.runner import run_configured_check
from specguard.config.models import CheckSpec
from specguard.models.status import CheckStatus
from specguard.project.detect import detect_project


def test_detects_maven_gradle_modules_and_wrappers(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("<project/>", encoding="utf-8")
    (tmp_path / "module-a").mkdir()
    (tmp_path / "module-a" / "pom.xml").write_text("<project/>", encoding="utf-8")
    (tmp_path / "build.gradle").write_text("plugins {}", encoding="utf-8")
    (tmp_path / "mvnw").write_text("#!/bin/sh\n", encoding="utf-8")
    (tmp_path / "gradlew").write_text("#!/bin/sh\n", encoding="utf-8")
    layout = detect_project(tmp_path)
    assert layout.systems == ["maven", "gradle"]
    assert "." in layout.modules
    assert "module-a" in layout.modules
    assert layout.maven_wrapper is True
    assert layout.gradle_wrapper is True
    assert layout.suggested_command is None


def test_unknown_layout_explains_the_limit(tmp_path: Path) -> None:
    layout = detect_project(tmp_path)
    assert layout.limitation
    assert "未猜测" in layout.limitation
    assert layout.suggested_command is None


def test_missing_command_is_not_guessed(tmp_path: Path) -> None:
    spec = CheckSpec(enabled=True, required=True, command=None)
    assert command_for(spec) is None
    result = run_configured_check("build", command_for(spec), True, True, 5, 100, tmp_path)
    assert result is not None
    assert result.status == CheckStatus.ERROR
    assert "不猜测" in (result.diagnostic or "")
