from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from specguard.project.detect import coverage_for
from tests.fixtures.materialize import commit_all, init_repo


def test_two_modules_are_not_separately_covered_and_one_module_is(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    for name in (".", "module-a", "module-b"):
        directory = repo if name == "." else repo / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "pom.xml").write_text("<project></project>\n", encoding="utf-8")
    coverage = coverage_for(
        repo,
        ["module-a/src/A.java", "module-b/src/B.java"],
        True,
    )
    assert coverage.execution == "repository"
    assert coverage.changed_modules == ["module-a", "module-b"]
    assert coverage.not_separately_covered == ["module-a", "module-b"]

    single = coverage_for(repo, ["module-a/src/A.java"], True)
    assert single.changed_modules == ["module-a"]
    assert single.not_separately_covered == []


def test_unrecognized_layout_and_unconfigured_checks_do_not_invent_a_command(tmp_path: Path) -> None:
    repo = tmp_path / "plain"
    repo.mkdir()
    (repo / "README.md").write_text("no build\n", encoding="utf-8")
    unrecognized = coverage_for(repo, ["src/A.java"], True)
    assert unrecognized.execution == "unrecognized"
    assert unrecognized.not_separately_covered == []

    built = tmp_path / "built"
    (built).mkdir()
    (built / "pom.xml").write_text("<project></project>\n", encoding="utf-8")
    idle = coverage_for(built, ["src/A.java"], False)
    assert idle.execution == "not_configured"
    assert idle.not_separately_covered == []


def test_repository_build_adds_a_skipped_module_separation_check(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    commit_all(repo, "base")
    from tests.fixtures.materialize import git

    git(repo, "checkout", "-b", "review")
    for name in ("module-a", "module-b"):
        source = repo / name / "src" / "Item.java"
        source.parent.mkdir(parents=True)
        source.write_text("class Item {}\n", encoding="utf-8")
        (repo / name / "pom.xml").write_text("<project></project>\n", encoding="utf-8")
    spec = repo / "openspec/changes/add-order/specs/order/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "## ADDED Requirements\n\n### Requirement: Create order\n\n系统必须创建订单并且保留记录。\n",
        encoding="utf-8",
    )
    config_path = repo / "specguard.yaml"
    config_path.write_text(
        "\n".join(
            [
                "version: 1",
                "artifacts:",
                "  provider: openspec",
                "  root: openspec",
                "git:",
                "  base: main",
                "  target: HEAD",
                "checks:",
                "  build:",
                "    enabled: true",
                "    required: false",
                '    command: "./mvnw -q -DskipTests package"',
                "  tests:",
                "    enabled: false",
                "security:",
                "  isolate_builds: false",
                "report:",
                "  output_dir: .specguard/reports",
                "  formats:",
                "    - markdown",
                "    - json",
                "",
            ]
        ),
        encoding="utf-8",
    )
    commit_all(repo, "two modules")
    report, _code = run_review(load_config(config_path), config_path, cli_subject="add-order")
    separation = next(item for item in report.checks if item.check_id == "module-separation")
    build = next(item for item in report.checks if item.check_id == "build")
    assert separation.status == "SKIPPED"
    assert separation.command is None
    assert "module-a" in (separation.diagnostic or "")
    assert "module-b" in (separation.diagnostic or "")
    assert build.command == "./mvnw -q -DskipTests package"
    assert build.status == "SKIPPED"
