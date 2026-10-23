import json
from pathlib import Path

import pytest

from specguard.errors import UsageError
from specguard.speckit.discover import feature_json_hint, list_features, select_feature


def _feature(root: Path, name: str, spec: bool = True) -> None:
    directory = root / "specs" / name
    directory.mkdir(parents=True)
    if spec:
        (directory / "spec.md").write_text("# feature\n", encoding="utf-8")


def test_only_numbered_directories_with_spec_are_candidates(tmp_path: Path) -> None:
    _feature(tmp_path, "001-sample")
    _feature(tmp_path, "notes")
    (tmp_path / "specs" / "002-empty").mkdir()
    assert list_features(tmp_path) == ["001-sample"]


def test_zero_candidates_selects_nothing(tmp_path: Path) -> None:
    assert list_features(tmp_path) == []
    assert select_feature([], None, None) is None


def test_one_candidate_is_selected(tmp_path: Path) -> None:
    _feature(tmp_path, "001-sample")
    names = list_features(tmp_path)
    assert select_feature(names, None, None) == "001-sample"


def test_many_candidates_require_an_explicit_name(tmp_path: Path) -> None:
    _feature(tmp_path, "001-a")
    _feature(tmp_path, "002-b")
    specify = tmp_path / ".specify"
    specify.mkdir()
    (specify / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-a"}),
        encoding="utf-8",
    )
    hint = feature_json_hint(tmp_path)
    with pytest.raises(UsageError) as caught:
        select_feature(list_features(tmp_path), None, hint)
    message = str(caught.value)
    assert "001-a" in message
    assert "002-b" in message
    assert hint is not None
    assert "feature.json" in message


def test_requested_feature_must_match_exactly() -> None:
    with pytest.raises(UsageError) as caught:
        select_feature(["001-sample"], "009-missing", None)
    assert "009-missing" in str(caught.value)
