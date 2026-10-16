import shutil
import subprocess
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def init_repo(repo: Path) -> None:
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)


def materialize(tmp: Path, name: str) -> Path:
    dest = tmp / name
    shutil.copytree(FIXTURES / name, dest)
    mvnw = dest / "mvnw"
    if mvnw.exists():
        mvnw.chmod(0o755)
    if name == "single_change":
        java = dest / "src/main/java/com/example/Order.java"
        java_text = java.read_text(encoding="utf-8")
        java.unlink()
        init_repo(dest)
        commit_all(dest, "base")
        git(dest, "checkout", "-b", "review")
        java.parent.mkdir(parents=True, exist_ok=True)
        java.write_text(java_text, encoding="utf-8")
        commit_all(dest, "add order code")
        return dest
    if (dest / "openspec").exists() or (dest / "specguard.yaml").exists():
        init_repo(dest)
        commit_all(dest, "base")
    return dest
