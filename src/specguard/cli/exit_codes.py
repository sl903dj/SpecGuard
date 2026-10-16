from specguard.models.status import ReviewStatus

OK = 0
INTERNAL = 1
POLICY_BLOCKED = 2
INCOMPLETE = 3
USAGE = 4


def exit_for(status: ReviewStatus) -> int:
    if status == ReviewStatus.POLICY_BLOCKED:
        return POLICY_BLOCKED
    if status == ReviewStatus.REVIEW_INCOMPLETE:
        return INCOMPLETE
    return OK
