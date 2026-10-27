from pathlib import Path

from specguard.git.diff import collect_changes, collect_tree_files
from specguard.pipeline import run_review
from tests.fixtures.materialize import commit_all, git
from tests.fixtures.review_gaps.materialize import blank_repo, write_config


def _current_repo(tmp_path: Path) -> Path:
    repo = blank_repo(tmp_path)
    outside = repo / "src/main/java/Outside.java"
    outside.parent.mkdir(parents=True)
    outside.write_text("class Outside { String id = \"order:create-order\"; }\n", encoding="utf-8")
    spec = repo / "openspec/specs/order/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "\n".join(
            [
                "## Requirements",
                "",
                "### Requirement: Create order",
                "",
                "系统必须创建订单，并保留标识。",
                "",
                "#### Scenario: 创建",
                "",
                "- THEN 系统必须返回订单号",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_config(repo)
    commit_all(repo, "current spec and existing code")
    git(repo, "checkout", "-b", "review")
    added = repo / "src/main/java/Note.java"
    added.write_text("class Note {}\n", encoding="utf-8")
    commit_all(repo, "note only")
    return repo


def test_range_ignores_files_outside_the_diff_and_tree_reads_target_blobs(tmp_path: Path) -> None:
    repo = _current_repo(tmp_path)
    config_path = write_config(repo)
    from specguard.config.loader import load_config

    config = load_config(config_path)
    report, code = run_review(config, config_path, baseline=True)
    assert code == 0
    assert report.metadata.evidence_scope == "range"
    assert "src/main/java/Outside.java" not in {item.path for item in report.changed_files}
    evidence = report.requirements[0].evidence[-1]
    assert evidence.status == "insufficient"
    assert evidence.file != "src/main/java/Outside.java"

    config.git.evidence_scope = "target_tree"
    ranged, code = run_review(config, config_path, baseline=True)
    assert code == 0
    assert ranged.metadata.evidence_scope == "target_tree"
    assert "src/main/java/Outside.java" not in {item.path for item in ranged.changed_files}
    assert ranged.requirements[0].evidence[-1].status == "direct"
    assert ranged.requirements[0].evidence[-1].file == "src/main/java/Outside.java"
    listed = {item.path for item in collect_tree_files(repo, "HEAD", False)}
    assert "src/main/java/Outside.java" in listed
    assert {item.path for item in collect_changes(repo, "main", "HEAD", False)} == {
        "src/main/java/Note.java"
    }


def test_uncommitted_files_enter_only_when_inclusion_is_enabled(tmp_path: Path) -> None:
    repo = _current_repo(tmp_path)
    extra = repo / "src/main/java/Pending.java"
    extra.write_text("class Pending { String id = \"order:create-order\"; }\n", encoding="utf-8")
    git(repo, "add", "src/main/java/Pending.java")
    hidden = {item.path for item in collect_tree_files(repo, "HEAD", False)}
    visible = {item.path for item in collect_tree_files(repo, "HEAD", True)}
    assert "src/main/java/Pending.java" not in hidden
    assert "src/main/java/Pending.java" in visible
    from specguard.config.loader import load_config

    config = load_config(write_config(repo))
    config.git.fail_on_uncommitted_changes = False
    config.git.evidence_scope = "target_tree"
    quiet, _code = run_review(config, repo / "specguard.yaml", baseline=True)
    assert "src/main/java/Pending.java" not in {item.path for item in quiet.changed_files}
    config.git.include_worktree = True
    included, _code = run_review(config, repo / "specguard.yaml", baseline=True)
    assert "src/main/java/Pending.java" in {item.path for item in included.changed_files}


def test_uncommitted_files_enter_only_when_inclusion_is_enabled(tmp_path: Path) -> None:
    repo = _current_repo(tmp_path)
    extra = repo / "src/main/java/Pending.java"
    extra.write_text("class Pending { String id = \"order:create-order\"; }\n", encoding="utf-8")
    git(repo, "add", "src/main/java/Pending.java")
    hidden = {item.path for item in collect_tree_files(repo, "HEAD", False)}
    visible = {item.path for item in collect_tree_files(repo, "HEAD", True)}
    assert "src/main/java/Pending.java" not in hidden
    assert "src/main/java/Pending.java" in visible
    from specguard.config.loader import load_config

    config = load_config(write_config(repo))
    config.git.fail_on_uncommitted_changes = False
    config.git.evidence_scope = "target_tree"
    quiet, _code = run_review(config, repo / "specguard.yaml", baseline=True)
    assert "src/main/java/Pending.java" not in {item.path for item in quiet.changed_files}
    config.git.include_worktree = True
    included, _code = run_review(config, repo / "specguard.yaml", baseline=True)
    assert "src/main/java/Pending.java" in {item.path for item in included.changed_files}


def test_uncommitted_files_enter_only_when_inclusion_is_enabled(tmp_path: Path) -> None:
    repo = _current_repo(tmp_path)
    extra = repo / "src/main/java/Pending.java"
    extra.write_text("class Pending { String id = \"order:create-order\"; }\n", encoding="utf-8")
    git(repo, "add", "src/main/java/Pending.java")
    hidden = {item.path for item in collect_tree_files(repo, "HEAD", False)}
    visible = {item.path for item in collect_tree_files(repo, "HEAD", True)}
    assert "src/main/java/Pending.java" not in hidden
    assert "src/main/java/Pending.java" in visible
    from specguard.config.loader import load_config

    config = load_config(write_config(repo))
    config.git.fail_on_uncommitted_changes = False
    config.git.evidence_scope = "target_tree"
    quiet, _code = run_review(config, repo / "specguard.yaml", baseline=True)
    assert "src/main/java/Pending.java" not in {item.path for item in quiet.changed_files}
    config.git.include_worktree = True
    included, _code = run_review(config, repo / "specguard.yaml", baseline=True)
    assert "src/main/java/Pending.java" in {item.path for item in included.changed_files}


def test_target_tree_on_a_change_fails_before_checks(tmp_path: Path) -> None:
    repo = blank_repo(tmp_path)
    change = repo / "openspec/changes/add-order/specs/order/spec.md"
    change.parent.mkdir(parents=True)
    change.write_text(
        "## ADDED Requirements\n\n### Requirement: Create order\n\n系统必须创建订单并且保留记录。\n",
        encoding="utf-8",
    )
    config_path = write_config(repo)
    commit_all(repo, "change")
    from specguard.config.loader import load_config

    config = load_config(config_path)
    config.git.evidence_scope = "target_tree"
    try:
        run_review(config, config_path, cli_subject="add-order")
    except Exception as exc:
        assert "完整内容证据范围只适用于当前规范" in str(exc)
    else:
        raise AssertionError("target_tree on a change must fail")
    assert not (repo / ".specguard/reports").exists() or not any((repo / ".specguard/reports").glob("*"))
