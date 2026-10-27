from pathlib import Path

from tests.fixtures.materialize import commit_all, init_repo


def write_config(repo: Path) -> Path:
    path = repo / "specguard.yaml"
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "artifacts:",
                "  provider: openspec",
                "  root: openspec",
                "git:",
                "  base: main",
                "  target: HEAD",
                "review:",
                "  mode: static",
                "  policy: advisory",
                "  llm_findings_block: false",
                "checks:",
                "  build:",
                "    enabled: false",
                "  tests:",
                "    enabled: false",
                "llm:",
                "  enabled: false",
                "  external_fallback: false",
                "security:",
                "  isolate_builds: false",
                "report:",
                "  formats:",
                "    - markdown",
                "    - json",
                "  output_dir: .specguard/reports",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def blank_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir(parents=True)
    init_repo(repo)
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    commit_all(repo, "base")
    return repo
