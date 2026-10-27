import tomllib
from pathlib import Path

from specguard import __version__

ROOT = Path(__file__).resolve().parents[2]


def test_console_script_is_the_install_entry() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["scripts"]["specguard"] == "specguard.cli.main:app"
    serialized = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    assert "pyinstaller" not in serialized
    assert "nuitka" not in serialized


def test_package_and_runtime_versions_are_0_4_0() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == "0.4.0"
    assert __version__ == "0.4.0"


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


def test_offline_install_lists_dependencies_and_readme_links() -> None:
    text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    assert "https://github.com/sl903dj/SpecGuard.git" in text
    assert "手工" in text
    assert "typer>=0.12" in text
    assert "pydantic>=2" in text
    assert "httpx>=0.27" in text
    assert "pyyaml>=6" in text
    assert "传递依赖" in text
    assert "pytest" in text and "不需要" in text
    assert "uv lock" in text
    assert "uv export --frozen --no-dev --no-emit-project" in text
    assert "pip download" in text
    assert "uv tool install --offline --no-index --find-links" in text
    assert "pypi.org" in text
    assert 'id="offline-install"' in text
    chinese = (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README.en.md").read_text(encoding="utf-8")
    assert "docs/install.md#offline-install" in chinese
    assert "docs/install.md#offline-install" in english
    assert 'uv tool install "git+https://github.com/sl903dj/SpecGuard"' in chinese
    assert 'uv tool install "git+https://github.com/sl903dj/SpecGuard"' in english


def test_offline_install_uses_checkout_root_and_setuptools() -> None:
    text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    assert "pyproject.toml" in text
    assert "不要传入 `src/specguard`" in text
    assert "setuptools>=68" in text
    assert 'pip download -r requirements.txt "setuptools>=68"' in text
    assert "build-system" in text
    assert "<检出根目录>" in text
    assert "<源码目录>" not in text


def test_empty_directory_is_only_for_version_check() -> None:
    text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    local, offline = text.split("## 内网离线安装", 1)
    phrase = "空目录是当前工作目录，不是安装位置"
    for section in (local, offline):
        assert "mkdir -p /tmp/specguard-install-check" in section
        assert phrase in section
        assert "安装之后" in section
        assert "不往里面写文件" in section
        assert section.index(phrase) < section.index("mkdir -p /tmp/specguard-install-check")
