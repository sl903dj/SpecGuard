import pytest

from specguard.errors import StatusRewriteError
from specguard.models.entities import CheckResult
from specguard.models.status import CheckStatus, parse_check_status, parse_review_status, rewrite_status


def test_unknown_status_rejected() -> None:
    with pytest.raises(ValueError):
        parse_check_status("NOPE")
    with pytest.raises(ValueError):
        parse_review_status("CLEAN")


def test_non_pass_cannot_become_pass() -> None:
    for current in (CheckStatus.SKIPPED, CheckStatus.ERROR, CheckStatus.TIMEOUT):
        with pytest.raises(StatusRewriteError):
            rewrite_status(current, CheckStatus.PASS)
        result = CheckResult(check_id="build", required=True, status=current)
        with pytest.raises(StatusRewriteError):
            result.rewrite(CheckStatus.PASS)
