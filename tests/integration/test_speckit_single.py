import json
import subprocess
from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize


def test_single_speckit_feature_writes_a_readonly_report(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "speckit_single")
    source = repo / "src/main/java/com/example/Order.java"
    before = source.read_bytes()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    config = load_config(repo / "specguard.yaml")
    report, code = run_review(config, repo / "specguard.yaml")
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    assert code == 0
    assert report.metadata.change == "001-sample"
    assert "001-sample" in text
    assert "需要人工审核" in text
    assert "需求覆盖" in text
    assert "潜在风险" in text
    assert "证据定位" in text
    assert report.metadata.limitations
    assert source.read_bytes() == before
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == head
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
    assert all(".specguard" in line or not line.strip() for line in status.splitlines())
    commands = " ".join(item.command or "" for item in report.checks)
    assert "specify" not in commands
