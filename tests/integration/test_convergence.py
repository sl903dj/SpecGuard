import subprocess
from pathlib import Path

from specguard.config.loader import load_config
from specguard.pipeline import run_review
from tests.fixtures.materialize import materialize


def test_review_reports_modules_build_risk_and_assisted_identity(tmp_path: Path) -> None:
    repo = materialize(tmp_path, "single_change")
    (repo / "pom.xml").write_text("<project></project>\n", encoding="utf-8")
    subprocess.run(["git", "add", "pom.xml"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add module"], cwd=repo, check=True)
    config = load_config(repo / "specguard.yaml")
    report, _code = run_review(config, repo / "specguard.yaml")
    text = Path(report.metadata.output_paths[0]).read_text(encoding="utf-8")
    assert "." in report.metadata.modules
    assert "识别到的构建模块" in text
    assert "项目自带脚本" in text
    assert "覆盖率分析不可用" in text
    assert report.summary.coverage_percent is None
    assert any("状态流转" in item for item in report.metadata.limitations)

    source = repo / "src/main/java/com/example/Order.java"
    source.write_text(source.read_text(encoding="utf-8") + "\n// api_key=supersecretvalue\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/main/java/com/example/Order.java"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "secret"], cwd=repo, check=True)
    data = config.model_dump()
    data["review"]["mode"] = "assisted"
    data["llm"]["enabled"] = True
    data["llm"]["base_url"] = "http://127.0.0.1:1/v1"
    data["llm"]["model"] = "local-model"
    data["llm"]["timeout_seconds"] = 1
    data["llm"]["external_fallback"] = False
    assisted = config.model_validate(data)
    assisted_report, _assisted_code = run_review(assisted, repo / "specguard.yaml")
    assisted_text = Path(assisted_report.metadata.output_paths[0]).read_text(encoding="utf-8")
    assert assisted_report.metadata.service_id == "127.0.0.1:1"
    assert assisted_report.metadata.model_id == "local-model"
    assert assisted_report.metadata.redactions
    assert "supersecretvalue" not in assisted_text
    assert "local-model" in assisted_text
