from specguard.llm.redact import redact
from specguard.models.entities import ChangedFile

SNIPPET_CHARS = 180


def limited_snippets(changed_files: list[ChangedFile], read_text, enabled: bool) -> list[str]:
    if not enabled:
        return []
    snippets: list[str] = []
    for item in changed_files:
        text = read_text(item.path) if read_text else ""
        cleaned, _notes = redact(text)
        compact = " ".join(cleaned.split())
        if not compact:
            continue
        snippets.append(f"{item.path}: {compact[:SNIPPET_CHARS]}")
    return snippets
