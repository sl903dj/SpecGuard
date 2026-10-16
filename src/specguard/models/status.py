from enum import Enum

from specguard.errors import StatusRewriteError


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class ReviewStatus(str, Enum):
    REVIEW_COMPLETE = "REVIEW_COMPLETE"
    REVIEW_INCOMPLETE = "REVIEW_INCOMPLETE"
    POLICY_BLOCKED = "POLICY_BLOCKED"


NON_PASS = {CheckStatus.SKIPPED, CheckStatus.ERROR, CheckStatus.TIMEOUT}


def parse_check_status(value: str) -> CheckStatus:
    try:
        return CheckStatus(value)
    except ValueError as exc:
        raise ValueError("检查状态只能是 PASS、FAIL、SKIPPED、ERROR、TIMEOUT 之一") from exc


def parse_review_status(value: str) -> ReviewStatus:
    try:
        return ReviewStatus(value)
    except ValueError as exc:
        raise ValueError(
            "整次状态只能是 REVIEW_COMPLETE、REVIEW_INCOMPLETE、POLICY_BLOCKED"
        ) from exc


def rewrite_status(current: CheckStatus, proposed: CheckStatus) -> CheckStatus:
    if current in NON_PASS and proposed == CheckStatus.PASS:
        raise StatusRewriteError("SKIPPED、ERROR、TIMEOUT 不能被写成 PASS")
    return proposed
