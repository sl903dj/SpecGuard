import re

from specguard.models.entities import ChangedFile, Requirement, Scenario, ScenarioAssessment
from specguard.review.test_adequacy import _trivial_assertion
from specguard.review.traceability import _cached_reader, _is_test_path

ASSERTION = re.compile(r"assert(?:True|False|Equals|NotNull|Null|That)\s*\(([^;]*)\)", re.I)


def _collapsed_lines(body: str) -> list[str]:
    lines = []
    for line in body.splitlines() or [body]:
        collapsed = re.sub(r"\s+", "", line)
        if len(collapsed) >= 8:
            lines.append(collapsed)
    if not lines:
        collapsed = re.sub(r"\s+", "", body)
        if len(collapsed) >= 8:
            lines.append(collapsed)
    return lines


def _supported_test(
    requirement: Requirement,
    scenario: Scenario,
    tests: list[tuple[str, str]],
) -> tuple[str, int] | None:
    expected = _collapsed_lines(scenario.body)
    if not expected:
        return None
    for path, text in tests:
        if requirement.identifier not in text and scenario.name not in text:
            continue
        matches = list(ASSERTION.finditer(text))
        nontrivial = [item for item in matches if not _trivial_assertion(item.group(1))]
        if not nontrivial:
            continue
        collapsed = re.sub(r"\s+", "", text)
        if not any(line in collapsed for line in expected):
            continue
        match = nontrivial[0]
        return path, text.count("\n", 0, match.start()) + 1
    return None


def assess_scenarios(
    requirements: list[Requirement],
    evidence_files: list[ChangedFile],
    read_text=None,
) -> list[ScenarioAssessment]:
    content_of = _cached_reader(read_text)
    tests: list[tuple[str, str]] = []
    for changed in evidence_files:
        if changed.change_type == "deleted" or not _is_test_path(changed.path):
            continue
        tests.append((changed.path, content_of(changed.path)))
    assessments: list[ScenarioAssessment] = []
    for requirement in requirements:
        if not requirement.scenarios:
            assessments.append(
                ScenarioAssessment(
                    requirement_id=requirement.identifier,
                    scenario_name=None,
                    status="unavailable",
                    note="场景审核不可用",
                )
            )
            continue
        for scenario in requirement.scenarios:
            found = _supported_test(requirement, scenario, tests)
            if found is None:
                note = (
                    "场景没有可核对的预期结果"
                    if not _collapsed_lines(scenario.body)
                    else "测试没有检查场景写出的预期结果"
                )
                assessments.append(
                    ScenarioAssessment(
                        requirement_id=requirement.identifier,
                        scenario_name=scenario.name,
                        status="gap",
                        note=note,
                    )
                )
                continue
            path, line = found
            assessments.append(
                ScenarioAssessment(
                    requirement_id=requirement.identifier,
                    scenario_name=scenario.name,
                    status="supported",
                    test_file=path,
                    test_line=line,
                    note="测试检查了场景写出的预期结果",
                )
            )
    return assessments
