from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture_root() -> Path:
    return FIXTURES
