import json
import subprocess
from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize


def test_review_writes_both_reports_and_leaves_sources_untouched(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    source = repo / "src/main/java/com/example/Order.java"
    before = source.read_bytes()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    config = load_config(repo / "specguard.yaml")
    report, code = run_review(config, repo / "specguard.yaml")
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    payload = json.loads(Path(report.metadata.output_paths[1]).read_text(encoding="utf-8"))
    assert code == 0
    assert "需要人工审核" in text
    assert "需求覆盖" in text
    assert "潜在风险" in text
    assert "证据定位" in text
    assert payload["schema_version"] == "1.0"
    assert payload["metadata"]["base"]
    assert payload["metadata"]["target"]
    assert source.read_bytes() == before
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == head
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
    assert all(".specguard" in line or not line.strip() for line in status.splitlines())
