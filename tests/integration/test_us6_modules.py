from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import commit_all, init_repo


def test_two_modules_are_named_and_the_repository_build_is_not_rewritten(tmp_path: Path) -> None:
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
    report, code = run_review(load_config(config_path), config_path, cli_subject="add-order")
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    build = next(item for item in report.checks if item.check_id == "build")
    separation = next(item for item in report.checks if item.check_id == "module-separation")
    assert code == 0
    assert report.metadata.module_coverage.not_separately_covered == ["module-a", "module-b"]
    assert separation.status == "SKIPPED"
    assert separation.command is None
    assert build.status == "SKIPPED"
    assert build.command == "./mvnw -q -DskipTests package"
    assert "仓库级命令没有按模块分别执行" in text
    assert "module-a" in text
    assert "module-b" in text
