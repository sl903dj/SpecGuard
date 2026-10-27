from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import commit_all
from tests.fixtures.review_gaps.materialize import blank_repo, write_config


def _repo(tmp_path: Path, *, with_current: bool, speckit: bool = False) -> tuple[Path, Path]:
    repo = blank_repo(tmp_path)
    if with_current:
        current = repo / "openspec/specs/order/spec.md"
        current.parent.mkdir(parents=True)
        current.write_text(
            "\n".join(
                [
                    "## Requirements",
                    "",
                    "### Requirement: Create order",
                    "",
                    "系统必须拒绝空数量。",
                    "",
                    "#### Scenario: 拒绝空数量",
                    "",
                    "系统必须拒绝空数量",
                    "",
                    "### Requirement: Ship notice",
                    "",
                    "系统必须发送发货通知给客户。",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    change = repo / "openspec/changes/add-order/specs/order/spec.md"
    change.parent.mkdir(parents=True)
    change.write_text(
        "\n".join(
            [
                "## ADDED Requirements",
                "",
                "### Requirement: Create order",
                "",
                "系统不得拒绝空数量。",
                "",
                "#### Scenario: 拒绝空数量",
                "",
                "系统不得拒绝空数量",
                "",
                "## MODIFIED Requirements",
                "",
                "### Requirement: Rename invoice",
                "",
                "系统不得沿用旧发票名称。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    modified_current = repo / "openspec/specs/order/spec.md"
    if with_current:
        modified_current.write_text(
            modified_current.read_text(encoding="utf-8")
            + "\n### Requirement: Rename invoice\n\n系统必须沿用旧发票名称。\n\n#### Scenario: 发票\n\n系统必须沿用旧发票名称\n",
            encoding="utf-8",
        )
    config_path = write_config(repo)
    commit_all(repo, "specs")
    return repo, config_path


def test_undeclared_conflict_is_reported_without_merging_current_requirements(tmp_path: Path) -> None:
    _repo_path, config_path = _repo(tmp_path, with_current=True)
    report, code = run_review(load_config(config_path), config_path, cli_subject="add-order")
    assert code == 0
    identifiers = {item.identifier for item in report.requirements}
    assert "order:ship-notice" not in identifiers
    conflicts = [item for item in report.consistency_items if item.status == "conflict"]
    assert len(conflicts) == 1
    assert conflicts[0].current_file.endswith("openspec/specs/order/spec.md")
    assert conflicts[0].change_file.endswith("openspec/changes/add-order/specs/order/spec.md")
    assert all(item.change_requirement_id != "add-order:modified:rename-invoice" or item.status != "conflict" for item in report.consistency_items)
    assert not any(
        item.status == "conflict" and "rename-invoice" in (item.change_requirement_id or "")
        for item in report.consistency_items
    )


def test_missing_current_spec_and_non_change_subjects_do_not_claim_a_comparison(tmp_path: Path) -> None:
    repo, config_path = _repo(tmp_path / "change-only", with_current=False)
    report, _code = run_review(load_config(config_path), config_path, cli_subject="add-order")
    assert "规范对照不可用" in report.metadata.limitations

    current_repo, current_config = _repo(tmp_path / "current", with_current=True)
    # Remove the change so this is current-only.
    import shutil

    shutil.rmtree(current_repo / "openspec/changes")
    from tests.fixtures.materialize import commit_all as commit

    commit(current_repo, "drop change")
    current, _code = run_review(load_config(current_config), current_config, baseline=True)
    assert "未做 OpenSpec 当前规范对照" in current.metadata.limitations

    from tests.fixtures.materialize import materialize_speckit
    import yaml

    speckit = materialize_speckit(tmp_path / "speckit")
    speckit_config = speckit / "specguard.yaml"
    speckit_config.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "artifacts": {"provider": "speckit", "root": "specs", "subject": "003-demo"},
                "git": {"base": "HEAD", "target": "HEAD", "fail_on_uncommitted_changes": False},
                "checks": {"build": {"enabled": False}, "tests": {"enabled": False}},
                "security": {"isolate_builds": False},
                "report": {"output_dir": ".specguard/reports", "formats": ["markdown", "json"]},
            }
        ),
        encoding="utf-8",
    )
    feature, _code = run_review(load_config(speckit_config), speckit_config)
    assert "未做 OpenSpec 当前规范对照" in feature.metadata.limitations
    assert feature.metadata.subject_id == "003-demo"
