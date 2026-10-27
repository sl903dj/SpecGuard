from pathlib import Path

import yaml

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from specguard.report.json_report import render_json
from specguard.report.markdown import render_markdown
from tests.fixtures.materialize import materialize_speckit


def test_explicit_speckit_review_is_traceable_and_read_only(tmp_path: Path) -> None:
    repo = materialize_speckit(tmp_path)
    config_path = repo / "specguard.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "artifacts": {
                    "provider": "speckit",
                    "root": "specs",
                    "subject": "003-demo",
                },
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
    feature = repo / "specs/003-demo"
    before = {path: path.read_bytes() for path in feature.rglob("*") if path.is_file()}
    report, _code = run_review(load_config(config_path), config_path)
    assert {item.identifier for item in report.requirements} == {"FR-001", "FR-002"}
    assert {item.identifier for item in report.tasks} == {"T001", "T002"}
    assert report.requirements[0].change_semantics is None
    assert report.summary.task_gap_count == 1
    payload = render_json(report)
    markdown = render_markdown(report)
    assert payload["schema_version"] == "1.3"
    assert payload["metadata"]["artifact_provider"] == "speckit"
    assert payload["metadata"]["subject_id"] == "003-demo"
    assert payload["artifacts"]["provider"] == "speckit"
    assert payload["artifacts"]["subject_id"] == "003-demo"
    assert len(payload["requirements"]) == len(report.requirements)
    assert payload["summary"]["task_gap_count"] == report.summary.task_gap_count
    assert f"工件提供方: {payload['artifacts']['provider']}" in markdown
    assert f"审核对象: {payload['artifacts']['subject_id']}" in markdown
    assert {item["kind"] for item in payload["artifacts"]["context_documents"]} >= {
        "plan",
        "research",
        "data_model",
        "contract",
        "quickstart",
        "checklist",
    }
    assert "任务 T001:" in markdown
    assert "任务 T002:" in markdown
    for document in payload["artifacts"]["context_documents"]:
        assert f"上下文 {document['kind']}: {document['path']}" in markdown
    for task in payload["tasks"]:
        assert f"任务 {task['identifier']}:" in markdown
        assert f"支撑 {task['support']}" in markdown
        assert f"{task['source_file']}:{task['source_line']}" in markdown
    assert {path.suffix for path in map(Path, report.metadata.output_paths)} == {".md", ".json"}
    assert before == {path: path.read_bytes() for path in feature.rglob("*") if path.is_file()}
