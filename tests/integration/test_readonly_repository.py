import subprocess
from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize


def test_review_does_not_change_git_history_or_sources(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    before = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True)
    tracked = subprocess.check_output(["git", "ls-files"], cwd=repo, text=True).splitlines()
    blobs = {
        path: (repo / path).read_bytes()
        for path in tracked
        if (repo / path).is_file()
    }
    config = load_config(repo / "specguard.yaml")
    run_review(config, repo / "specguard.yaml")
    after = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True)
    assert before == after
    assert subprocess.check_output(["git", "diff"], cwd=repo, text=True) == ""
    for path, content in blobs.items():
        assert (repo / path).read_bytes() == content
