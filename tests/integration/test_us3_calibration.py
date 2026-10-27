import json
from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import commit_all
from tests.fixtures.review_gaps.materialize import blank_repo, write_config

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "review_gaps" / "calibration"


def _repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = blank_repo(tmp_path)
    spec = repo / "openspec/changes/add-order/specs/order/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "## ADDED Requirements\n\n### Requirement: Create order\n\n系统必须创建订单并且保留记录。\n",
        encoding="utf-8",
    )
    config_path = write_config(repo)
    commit_all(repo, "change")
    return repo, config_path


def _review(repo: Path, config_path: Path, ledger: str | None):
    report_dir = repo / ".specguard" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    target = report_dir / "calibration.json"
    if target.exists():
        target.unlink()
    if ledger is not None:
        target.write_text((FIXTURES / ledger).read_text(encoding="utf-8"), encoding="utf-8")
    config = load_config(config_path)
    config.git.fail_on_uncommitted_changes = False
    return run_review(config, config_path, cli_subject="add-order")


def test_four_ledgers_redact_secrets_and_stay_advisory(tmp_path: Path) -> None:
    repo, config_path = _repo(tmp_path)
    missing, missing_code = _review(repo, config_path, None)
    assert missing_code == 0
    assert missing.policy.blocked is False
    assert missing.metadata.calibration.status == "incomplete"
    assert "历史对照未完成" in missing.metadata.calibration.notes

    incomplete, incomplete_code = _review(repo, config_path, "incomplete.json")
    assert incomplete_code == 0
    assert incomplete.policy.blocked is False
    assert incomplete.metadata.calibration.status == "incomplete"
    assert "历史对照未完成" in incomplete.metadata.calibration.notes

    rejected, rejected_code = _review(repo, config_path, "false_complete.json")
    assert rejected_code == 0
    assert rejected.metadata.calibration.status == "incomplete"
    assert rejected.metadata.calibration.rejected_complete_mark is True
    assert "完成标记已拒绝" in rejected.metadata.calibration.notes
    assert rejected.metadata.output_paths

    done, done_code = _review(repo, config_path, "complete.json")
    assert done_code == 0
    assert done.policy.blocked is False
    assert done.metadata.calibration.status == "complete"
    assert done.metadata.calibration.completed_review_count == 1

    secret, secret_code = _review(repo, config_path, "secret.json")
    assert secret_code == 0
    assert secret.policy.blocked is False
    assert secret.metadata.calibration.status == "complete"
    rendered = json.dumps(secret.model_dump(), ensure_ascii=False)
    assert "supersecretvalue" not in rendered
    assert any(item.category == "credential" for item in secret.metadata.redactions)
