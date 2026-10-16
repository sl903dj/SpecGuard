import json
from pathlib import Path

import httpx
import pytest

from specguard.config.loader import load_config
from specguard.models.status import CheckStatus
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize


def test_static_mode_skips_assisted_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_args, **_kwargs):
        raise AssertionError("静态模式不应创建 HTTP 客户端")

    monkeypatch.setattr(httpx.Client, "__init__", explode)
    repo = materialize(tmp_path, "single_change")
    config = load_config(repo / "specguard.yaml")
    report, code = run_review(config, repo / "specguard.yaml")
    assisted = [item for item in report.checks if item.check_id.startswith("assisted")]
    assert assisted
    assert all(item.status == CheckStatus.SKIPPED for item in assisted)
    assert any(item.check_id == "build" and item.status == CheckStatus.PASS for item in report.checks)
    assert code == 0
    payload = json.loads(Path(report.metadata.output_paths[1]).read_text(encoding="utf-8"))
    assert payload["policy"]["mode"] == "advisory"
