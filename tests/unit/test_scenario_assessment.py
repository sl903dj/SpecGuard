from specguard.models.entities import ChangedFile, Requirement, Scenario
from specguard.review.assisted import merge_llm_output
from specguard.review.scenarios import assess_scenarios
from specguard.review.traceability import link_requirements


def _requirement(identifier: str, title: str, body: str, scenarios: list[Scenario] | None = None) -> Requirement:
    return Requirement(
        identifier=identifier,
        title=title,
        change_semantics="added",
        scenarios=scenarios or [],
        source_file="specs/order/spec.md",
        source_line=3,
        body=body,
    )


def test_primary_evidence_uses_fixed_notes() -> None:
    direct = _requirement("add-order:added:create-order", "Create order", "Create an order record.")
    inferred = _requirement("add-order:added:save-file", "Save file", "Touch Order.java only by name.")
    missing = _requirement("add-order:added:quiet", "Quiet rule", "No file name is mentioned here.")
    files = [
        ChangedFile(path="src/main/java/Order.java", change_type="modified"),
        ChangedFile(path="src/main/java/Other.java", change_type="modified"),
    ]

    def read_text(path: str) -> str:
        if path.endswith("Order.java"):
            return "class Order { String id = \"add-order:added:create-order\"; }\n"
        return "class Other {}\n"

    link_requirements([direct, inferred, missing], files, read_text)
    assert direct.evidence[-1].status == "direct"
    assert direct.evidence[-1].note == "只代表找到关联，不代表验收场景已经通过"
    assert inferred.evidence[-1].status == "inferred"
    assert inferred.evidence[-1].note == "不能单独证明需求已经实现"
    assert missing.evidence[-1].status == "insufficient"
    assert missing.evidence[-1].note == "找不到实现证据"


def test_scenario_support_requires_nontrivial_expected_text() -> None:
    scenario = Scenario(name="Happy path", source_line=8, body="- THEN an order id is returned")
    empty = Scenario(name="No outcome", source_line=12, body="短")
    requirement = _requirement(
        "add-order:added:create-order",
        "Create order",
        "Create an order record.",
        [scenario, empty],
    )
    bare = _requirement("add-order:added:bare", "Bare rule", "This requirement has no scenario heading.")
    good = ChangedFile(path="src/test/java/OrderTest.java", change_type="added")
    trivial = ChangedFile(path="src/test/java/TrivialTest.java", change_type="added")

    def read_text(path: str) -> str:
        if path.endswith("OrderTest.java"):
            return (
                "class OrderTest {\n"
                "  void ok() {\n"
                "    // add-order:added:create-order\n"
                "    // - THEN an order id is returned\n"
                "    assertEquals(orderId, result);\n"
                "  }\n"
                "}\n"
            )
        return "class TrivialTest { void t() { assertTrue(true); } }\n"

    found = {item.scenario_name: item for item in assess_scenarios([requirement, bare], [good, trivial], read_text)}
    assert found["Happy path"].status == "supported"
    assert found["Happy path"].test_file == "src/test/java/OrderTest.java"
    assert found["Happy path"].test_line == 5
    assert found["No outcome"].status == "gap"
    assert found["No outcome"].note == "场景没有可核对的预期结果"
    assert found[None].status == "unavailable"
    assert found[None].note == "场景审核不可用"


def test_assisted_claim_does_not_mark_a_scenario_supported() -> None:
    scenario = Scenario(name="Happy path", source_line=4, body="- THEN an order id is returned")
    requirement = _requirement("order:create-order", "Create order", "Create an order.", [scenario])
    before = assess_scenarios([requirement], [], lambda _path: "")
    merge_llm_output(
        {
            "findings": [
                {
                    "summary": "scenario supported",
                    "category": "test_adequacy",
                    "file": "src/test/java/OrderTest.java",
                    "line": 3,
                }
            ]
        },
        {"src/test/java/OrderTest.java"},
    )
    after = assess_scenarios([requirement], [], lambda _path: "")
    assert before[0].status == "gap"
    assert after[0].status == "gap"
    assert after[0].note == "测试没有检查场景写出的预期结果"
