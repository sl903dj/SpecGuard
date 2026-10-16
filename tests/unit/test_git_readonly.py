from pathlib import Path

import pytest

from specguard.errors import ReadOnlyError, UsageError
from specguard.git.diff import parse_name_status
from specguard.git.repository import discover_root, resolve_revision, run_git
from tests.fixtures.materialize import init_repo, commit_all


def test_mutating_git_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ReadOnlyError):
        run_git(["add", "."], tmp_path)
    for command in ("commit", "checkout", "reset", "merge", "clean"):
        with pytest.raises(ReadOnlyError):
            run_git([command], tmp_path)


def test_directory_outside_git_stops(tmp_path: Path) -> None:
    with pytest.raises(UsageError) as exc:
        discover_root(tmp_path)
    assert "版本库" in str(exc.value)


def test_unknown_revision_is_not_replaced(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    commit_all(tmp_path, "init")
    head = resolve_revision(tmp_path, "HEAD")
    with pytest.raises(UsageError) as exc:
        resolve_revision(tmp_path, "zzzz-not-a-rev")
    assert "zzzz-not-a-rev" in str(exc.value)
    assert resolve_revision(tmp_path, "HEAD") == head


def test_rename_status_parses() -> None:
    files = parse_name_status("R100\told.txt\tnew.txt\nD\tgone.txt\n", committed=True)
    renamed = files[0]
    assert renamed.change_type == "renamed"
    assert renamed.previous_path == "old.txt"
    assert renamed.path == "new.txt"
    assert files[1].change_type == "deleted"
