import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_console_script_is_the_install_entry() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["scripts"]["specguard"] == "specguard.cli.main:app"
    serialized = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    assert "pyinstaller" not in serialized
    assert "nuitka" not in serialized


def test_install_doc_does_not_require_cloning_into_the_reviewed_repo() -> None:
    text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    assert "命令路径" in text
    assert "被审核" in text
    assert "不克隆" in text or "不把 SpecGuard 源码" in text
    assert "原生二进制" in text
    assert "源码检出" in text
    assert 'uv tool install "git+https://github.com/sl903dj/SpecGuard"' in text
    assert "uv tool install --force" in text
    assert "src/specguard" in text
    assert "specguard version" in text
    assert "uv tool install specguard" not in text


def test_apache_license_metadata() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["license"] == "Apache-2.0"
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0" in license_text
    assert "Copyright 2026 sl903dj" in license_text


def test_bilingual_readmes_link_install_and_license() -> None:
    chinese = (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README.en.md").read_text(encoding="utf-8")
    assert "README.en.md" in chinese[:400]
    assert "README.md" in english[:400]
    for text in (chinese, english):
        assert "git+https://github.com/sl903dj/SpecGuard" in text
        assert "specguard version" in text
        assert "src/specguard" in text
        assert "LICENSE" in text
        assert "uv tool install --force" in text
    assert "质量门" in chinese
    assert "编程助手" not in chinese
    assert "合并门禁" not in chinese
    assert "quality gate" in english.lower()
    assert "coding assistant" not in english.lower()
    assert "merge gate" not in english.lower()
