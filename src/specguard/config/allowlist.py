import shlex
from pathlib import Path

ALLOWED_BASENAMES = {
    "mvn",
    "mvnw",
    "mvnw.cmd",
    "gradle",
    "gradlew",
    "gradlew.bat",
    "checkstyle",
    "spotbugs",
    "pmd",
    "java",
    "openspec",
}


def command_allowed(command: str) -> bool:
    if any(token in command for token in (";", "|", "&&", "||", "`", "$(", "\n")):
        return False
    try:
        argv = shlex.split(command)
    except ValueError:
        return False
    if not argv:
        return False
    base = Path(argv[0]).name.lower()
    return base in ALLOWED_BASENAMES
