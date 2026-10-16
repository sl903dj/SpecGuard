import re

REDACTIONS = (
    ("credential", re.compile(r"(?i)(api[_-]?key|password|secret)\s*[:=]\s*\S+")),
    ("token", re.compile(r"(?i)bearer\s+\S+")),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
)


def redact(text: str) -> tuple[str, list[dict]]:
    notes: list[dict] = []
    cleaned = text
    for category, pattern in REDACTIONS:
        matches = list(pattern.finditer(cleaned))
        if not matches:
            continue
        notes.append({"category": category, "count": len(matches)})
        cleaned = pattern.sub(f"[REDACTED:{category}]", cleaned)
    return cleaned, notes
