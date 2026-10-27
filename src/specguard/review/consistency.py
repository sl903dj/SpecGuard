import re

from specguard.models.entities import ConsistencyItem, Requirement
from specguard.openspec.parser import _slug

POSITIVE = ("必须", "应当", "需要")
NEGATIVE = ("不得", "禁止", "不再")


def _polarity(text: str) -> tuple[bool, bool]:
    return any(word in text for word in POSITIVE), any(word in text for word in NEGATIVE)


def _shared_phrase(left: str, right: str, title: str) -> bool:
    if len(title) >= 2 and title in left and title in right:
        return True
    for run in re.findall(r"[\u4e00-\u9fff]{2,}", left):
        for index in range(len(run) - 1):
            if run[index : index + 2] in right:
                return True
    left_ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,}", left))
    right_ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,}", right))
    return bool(left_ids & right_ids)


def _opposes(left: str, right: str, title: str) -> bool:
    left_pos, left_neg = _polarity(left)
    right_pos, right_neg = _polarity(right)
    opposite = (left_pos and right_neg) or (left_neg and right_pos)
    return opposite and _shared_phrase(left, right, title)


def compare_current_spec(
    change_requirements: list[Requirement],
    current_requirements: list[Requirement],
) -> list[ConsistencyItem]:
    current_by: dict[tuple[str, str], Requirement] = {}
    for requirement in current_requirements:
        current_by[(requirement.capability or "", _slug(requirement.title))] = requirement
    change_by: dict[tuple[str, str], list[Requirement]] = {}
    for requirement in change_requirements:
        key = (requirement.capability or "", _slug(requirement.title))
        change_by.setdefault(key, []).append(requirement)
    items: list[ConsistencyItem] = []
    for key, current in current_by.items():
        related = change_by.get(key, [])
        if not related or any(item.change_semantics in {"modified", "removed"} for item in related):
            continue
        for change in related:
            paired = False
            conflict = False
            current_scenarios = {item.name: item for item in current.scenarios}
            for scenario in change.scenarios:
                other = current_scenarios.get(scenario.name)
                if other is None:
                    continue
                paired = True
                if _opposes(other.body, scenario.body, current.title):
                    conflict = True
                    break
            if conflict:
                items.append(
                    _item(
                        current,
                        change,
                        "conflict",
                        "变更否定了当前规范中仍然有效的场景，且没有声明修改或删除",
                    )
                )
                continue
            bodies_differ = current.body.strip() != change.body.strip()
            if bodies_differ or (paired and not conflict and current.body.strip() != change.body.strip()):
                items.append(_item(current, change, "human_review", "无法判断是否冲突"))
    return items


def _item(
    current: Requirement,
    change: Requirement,
    status: str,
    summary: str,
) -> ConsistencyItem:
    return ConsistencyItem(
        capability=current.capability or "",
        current_requirement_id=current.identifier,
        current_file=current.source_file,
        current_line=current.source_line,
        change_requirement_id=change.identifier,
        change_file=change.source_file,
        change_line=change.source_line,
        status=status,  # type: ignore[arg-type]
        summary=summary,
    )
