from pathlib import Path

from specguard.checks.isolate import isolated_root


def test_isolation_failure_is_reported(tmp_path: Path) -> None:
    def boom(*_args, **_kwargs):
        raise OSError("cannot copy")

    dest, error = isolated_root(tmp_path, True, copytree=boom)
    assert dest is None
    assert error
