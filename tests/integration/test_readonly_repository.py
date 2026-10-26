import subprocess
from pathlib import Path

import yaml

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize, materialize_speckit


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


def test_speckit_review_preserves_artifacts_state_index_and_history(
    tmp_path: Path,
) -> None:
    repo = materialize_speckit(tmp_path)
    config_path = repo / "specguard.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "artifacts": {"provider": "speckit", "root": "specs"},
                "git": {
                    "base": "HEAD",
                    "target": "HEAD",
                    "fail_on_uncommitted_changes": False,
                },
                "report": {"output_dir": ".specguard/reports", "formats": ["markdown", "json"]},
            }
        ),
        encoding="utf-8",
    )
    watched = [
        path
        for root in (repo / "specs", repo / ".specify")
        for path in root.rglob("*")
        if path.is_file()
    ]
    contents = {path.relative_to(repo): path.read_bytes() for path in watched}
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo)
    index = subprocess.check_output(["git", "diff", "--cached", "--binary"], cwd=repo)

    run_review(load_config(config_path), config_path)

    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo) == head
    assert subprocess.check_output(
        ["git", "diff", "--cached", "--binary"], cwd=repo
    ) == index
    assert contents == {
        path.relative_to(repo): path.read_bytes() for path in watched
    }


def test_disabled_isolation_does_not_run_commands_in_repository(tmp_path: Path) -> None:
    repo = materialize_speckit(tmp_path)
    script = repo / "mvnw"
    script.write_text("#!/bin/sh\ntouch touched-by-check\n", encoding="utf-8")
    script.chmod(0o755)
    config_path = repo / "specguard.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "artifacts": {"provider": "speckit", "subject": "003-demo"},
                "git": {"base": "HEAD", "target": "HEAD", "fail_on_uncommitted_changes": False},
                "checks": {"build": {"enabled": True, "required": True, "command": "./mvnw -q package"}},
                "security": {"isolate_builds": False},
                "report": {"formats": ["markdown", "json"]},
            }
        ),
        encoding="utf-8",
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo)
    index = subprocess.check_output(["git", "diff", "--cached", "--binary"], cwd=repo)
    run_review(load_config(config_path), config_path)
    assert not (repo / "touched-by-check").exists()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo) == head
    assert subprocess.check_output(["git", "diff", "--cached", "--binary"], cwd=repo) == index
    assert subprocess.check_output(["git", "diff", "--", "specs", ".specify"], cwd=repo, text=True) == ""
