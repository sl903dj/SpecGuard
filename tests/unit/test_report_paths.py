from pathlib import Path

import pytest

from specguard.errors import UsageError
from specguard.report.paths import resolve_report_dir


def test_report_dir_must_stay_inside_reports(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / ".specguard" / "reports").mkdir(parents=True)
    resolved = resolve_report_dir(repo, ".specguard/reports")
    assert resolved == (repo / ".specguard" / "reports").resolve()


def test_parent_escape_rejected(tmp_path: Path) -> None:
    with pytest.raises(UsageError):
        resolve_report_dir(tmp_path, "../outside")


def test_git_metadata_rejected(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    with pytest.raises(UsageError):
        resolve_report_dir(tmp_path, ".git/config")


def test_source_file_rejected(tmp_path: Path) -> None:
    with pytest.raises(UsageError):
        resolve_report_dir(tmp_path, "src/Main.java")
