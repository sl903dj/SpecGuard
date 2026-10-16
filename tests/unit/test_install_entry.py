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
