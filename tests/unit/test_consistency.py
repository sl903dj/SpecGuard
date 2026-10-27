from specguard.models.entities import Requirement, Scenario
from specguard.review.consistency import compare_current_spec


def _req(identifier: str, title: str, body: str, capability: str, semantics: str | None, scenarios: list[Scenario]) -> Requirement:
    return Requirement(
        identifier=identifier,
        title=title,
        capability=capability,
        change_semantics=semantics,  # type: ignore[arg-type]
        scenarios=scenarios,
        source_file=f"{capability}/spec.md",
        source_line=4,
        body=body,
    )


def test_opposite_scenario_without_declaration_is_a_conflict() -> None:
    current = _req(
        "order:create-order",
        "Create order",
        "系统必须拒绝空数量",
        "order",
        None,
        [Scenario(name="拒绝空数量", source_line=6, body="系统必须拒绝空数量")],
    )
    change = _req(
        "add-order:added:create-order",
        "Create order",
        "系统不得拒绝空数量",
        "order",
        "added",
        [Scenario(name="拒绝空数量", source_line=8, body="系统不得拒绝空数量")],
    )
    only_current = _req(
        "order:ship-notice",
        "Ship notice",
        "系统必须发送通知",
        "order",
        None,
        [],
    )
    items = compare_current_spec([change], [current, only_current])
    assert len(items) == 1
    assert items[0].status == "conflict"
    assert items[0].current_requirement_id == "order:create-order"
    assert items[0].change_requirement_id == "add-order:added:create-order"
    assert items[0].current_line == 4
    assert items[0].change_line == 4


def test_declared_modification_is_not_a_conflict() -> None:
    current = _req(
        "order:create-order",
        "Create order",
        "系统必须拒绝空数量",
        "order",
        None,
        [Scenario(name="拒绝空数量", source_line=6, body="系统必须拒绝空数量")],
    )
    change = _req(
        "add-order:modified:create-order",
        "Create order",
        "系统不得拒绝空数量",
        "order",
        "modified",
        [Scenario(name="拒绝空数量", source_line=8, body="系统不得拒绝空数量")],
    )
    assert compare_current_spec([change], [current]) == []


def test_unclear_wording_is_human_review_and_other_capabilities_do_not_pair() -> None:
    current = _req(
        "order:create-order",
        "Create order",
        "系统必须创建订单",
        "order",
        None,
        [Scenario(name="创建", source_line=6, body="系统必须创建订单")],
    )
    change = _req(
        "add-order:added:create-order",
        "Create order",
        "系统必须创建订单并通知仓库",
        "order",
        "added",
        [Scenario(name="创建", source_line=8, body="系统必须创建订单并通知仓库")],
    )
    other = _req(
        "billing:create-order",
        "Create order",
        "系统不得创建订单",
        "billing",
        "added",
        [Scenario(name="创建", source_line=9, body="系统不得创建订单")],
    )
    items = compare_current_spec([change, other], [current])
    assert len(items) == 1
    assert items[0].status == "human_review"
    assert items[0].summary == "无法判断是否冲突"
