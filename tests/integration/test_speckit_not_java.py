from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize


def test_non_java_speckit_repo_does_not_claim_success(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "speckit_not_java")
    config = load_config(repo / "specguard.yaml")
    report, _code = run_review(config, repo / "specguard.yaml")
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    assert any(item.identifier == "FR-001" for item in report.requirements)
    assert "无法可靠识别 Java 项目布局。未猜测构建命令。" in report.metadata.limitations
    for check in report.checks:
        command = check.command or ""
        assert "mvn" not in command
        assert "gradle" not in command
    assert "需求符合性已经通过" not in text
    assert "代码风险已经通过" not in text
    assert "测试已经通过" not in text
    assert all(
        evidence.status != "direct"
        for requirement in report.requirements
        for evidence in requirement.evidence
    )
