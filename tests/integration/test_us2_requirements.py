import json
from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize


def test_requirement_and_task_gaps_are_not_called_defects(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    config = load_config(repo / "specguard.yaml")
    report, _code = run_review(config, repo / "specguard.yaml")
    payload = json.loads(Path(report.metadata.output_paths[1]).read_text(encoding="utf-8"))
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    requirement = payload["requirements"][0]
    assert requirement["evidence"][-1]["status"] == "insufficient"
    completed = next(item for item in payload["tasks"] if item["identifier"] == "1.1")
    assert completed["support"] == "none"
    assert all("代码一定有错" not in item["summary"] for item in payload["findings"])
    assert any(item["category"] == "task_integrity" for item in payload["findings"])
    assert "proposal.md" in payload["artifacts"]["found"]
