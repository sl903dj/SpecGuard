import time
from pathlib import Path

from specguard.openspec.parser import load_current


def test_parse_1000_current_requirements_under_five_seconds(tmp_path: Path) -> None:
    root = tmp_path / "openspec"
    for capability in range(100):
        lines: list[str] = []
        for index in range(10):
            lines.extend(
                [
                    f"### Requirement: Capability {capability} item {index}",
                    "",
                    f"The system handles item {index} for capability {capability} with a concrete outcome.",
                    "",
                    "#### Scenario: Done",
                    "",
                    "- WHEN requested",
                    "- THEN stored",
                    "",
                ]
            )
        path = root / "specs" / f"cap-{capability:03d}" / "spec.md"
        path.parent.mkdir(parents=True)
        path.write_text("\n".join(lines), encoding="utf-8")
    started = time.perf_counter()
    found, requirements = load_current(root)
    elapsed = time.perf_counter() - started
    assert len(found) == 100
    assert len(requirements) == 1000
    assert elapsed < 5
