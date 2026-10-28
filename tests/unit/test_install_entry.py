import tomllib
from pathlib import Path

from specguard import __version__

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INSTALL = 'uv tool install "git+https://github.com/sl903dj/SpecGuard"'
BRANCH_INSTALL_ZH = 'uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"'
BRANCH_INSTALL_EN = 'uv tool install "git+https://github.com/sl903dj/SpecGuard@<branch>"'


def _section(text: str, heading: str) -> str:
    start = text.index(heading + "\n")
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]
DEFAULT_INSTALL = 'uv tool install "git+https://github.com/sl903dj/SpecGuard"'
BRANCH_INSTALL_ZH = 'uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"'
BRANCH_INSTALL_EN = 'uv tool install "git+https://github.com/sl903dj/SpecGuard@<branch>"'


def _section(text: str, heading: str) -> str:
    start = text.index(heading + "\n")
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


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


def test_default_install_names_master_branch() -> None:
    chinese = _section((ROOT / "README.md").read_text(encoding="utf-8"), "## 安装")
    install = _section((ROOT / "docs" / "install.md").read_text(encoding="utf-8"), "## 使用者")
    english = _section((ROOT / "README.en.md").read_text(encoding="utf-8"), "## Install")
    for section in (chinese, install):
        assert DEFAULT_INSTALL in section
        assert "默认分支" in section
        assert "`master`" in section
        assert "未合并" in section
    assert DEFAULT_INSTALL in english
    assert "default branch" in english
    assert "`master`" in english
    assert "not merged" in english


def test_docs_explain_branch_install() -> None:
    install_text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    assert BRANCH_INSTALL_ZH in (ROOT / "README.md").read_text(encoding="utf-8")
    assert BRANCH_INSTALL_ZH in install_text
    assert BRANCH_INSTALL_EN in (ROOT / "README.en.md").read_text(encoding="utf-8")
    users = _section(install_text, "## 使用者")
    for phrase in (
        'uv tool install "git+https://github.com/sl903dj/SpecGuard@005-close-review-gaps"',
        'uv tool install --force "git+https://github.com/sl903dj/SpecGuard@<分支名>"',
        'uv tool install --force "git+https://github.com/sl903dj/SpecGuard"',
        "uv tool upgrade",
        "git ls-remote --heads https://github.com/sl903dj/SpecGuard",
        "https://github.com/sl903dj/SpecGuard/branches",
        "安装失败",
        "离线安装",
    ):
        assert phrase in users, phrase


def test_version_check_follows_installed_branch() -> None:
    install = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    operations = (ROOT / "docs" / "operations.md").read_text(encoding="utf-8")
    assert "应输出 `0.4.0`" not in install
    assert "与所装分支" in install
    assert "`0.1.0`" in install
    assert "得到 `0.4.0`" not in operations
    assert "确认输出 `0.4.0`" not in operations
    assert "与所装分支" in operations


def test_offline_install_selects_branch() -> None:
    text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    offline = text.split("## 内网离线安装", 1)[1]
    assert "git clone --branch <分支名> https://github.com/sl903dj/SpecGuard.git" in offline
    assert "不加 `--branch`" in offline
    assert "`master`" in offline


def test_docs_explain_uninstall() -> None:
    text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    for name in ("README.md", "README.en.md"):
        readme = (ROOT / name).read_text(encoding="utf-8")
        assert "uv tool uninstall specguard" in readme
        assert "docs/install.md#uninstall" in readme
    assert '<a id="uninstall"></a>' in text
    assert text.index("## 卸载") > text.index("## 开发者")
    uninstall = _section(text, "## 卸载")
    for phrase in (
        "uv tool uninstall specguard",
        "默认分支",
        "指定分支",
        "本地检出",
        "离线安装",
        "command -v specguard",
        "hash -r",
        "specguard.yaml",
        ".specguard/reports/",
        "calibration.json",
        "保留",
        "手工删除",
        "uv cache clean specguard",
        "可选",
        "`specguard` is not installed",
        "不需要联网",
        "/tmp/specguard-wheels",
        "不需要先卸载",
        ".venv",
    ):
        assert phrase in uninstall, phrase
    assert "rm " not in uninstall


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
