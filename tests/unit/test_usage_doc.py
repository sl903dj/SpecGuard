from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_usage_doc_follows_install_order() -> None:
    text = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")
    markers = [
        "specguard version",
        ".git",
        "openspec/changes/",
        "version: 1",
        "git.base",
        "specguard config validate --config specguard.yaml",
        "未提交改动时停止审核",
        "specguard review --config specguard.yaml --mode static --policy advisory",
        ".specguard/reports",
        "docs/report-interpretation.md",
    ]
    positions = [text.index(marker) for marker in markers]
    assert positions == sorted(positions)
    review_at = positions[-3]
    assert text.index("--policy strict") > review_at
    assert text.index("--mode assisted") > review_at
    assert "可选" in text[review_at:]
    assert "空目录" in text
    assert "安装验证" in text
    assert "被审核仓库" in text
    assert "不合并" in text
    assert "编程助手" not in text
    assert "合并门禁" not in text

    install = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    user_section = install.split("## 验证本地源码", 1)[0]
    assert "docs/usage.md" in user_section
    assert "docs/usage.md" in (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README.en.md").read_text(encoding="utf-8")
    assert "docs/usage.md" in english
    assert (
        "specguard review --config specguard.yaml --mode static --policy advisory"
        not in english
    )
