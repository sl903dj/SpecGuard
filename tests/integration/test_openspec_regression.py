import subprocess
from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize


def test_openspec_review_keeps_change_selection_and_readonly_result(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    config = load_config(repo / "specguard.yaml")
    report, code = run_review(config, repo / "specguard.yaml")
    assert code == 0
    assert report.metadata.change == "add-order"
    statuses = {
        evidence.status
        for requirement in report.requirements
        for evidence in requirement.evidence
    }
    assert statuses
    assert statuses <= {"direct", "inferred", "insufficient"}
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == head
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
    assert all(".specguard" in line or not line.strip() for line in status.splitlines())
