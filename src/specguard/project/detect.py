from pathlib import Path

from pydantic import BaseModel, ConfigDict


class ProjectLayout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    systems: list[str]
    modules: list[str]
    maven_wrapper: bool
    gradle_wrapper: bool
    limitation: str | None = None
    suggested_command: str | None = None


def detect_project(repo: Path) -> ProjectLayout:
    pom_files = sorted(repo.rglob("pom.xml"))
    gradle_files = sorted(repo.rglob("build.gradle")) + sorted(repo.rglob("build.gradle.kts"))
    systems: list[str] = []
    if pom_files:
        systems.append("maven")
    if gradle_files:
        systems.append("gradle")
    modules = sorted(
        {str(path.parent.relative_to(repo)) if path.parent != repo else "." for path in [*pom_files, *gradle_files]}
    )
    maven_wrapper = (repo / "mvnw").is_file()
    gradle_wrapper = (repo / "gradlew").is_file()
    limitation = None
    if not systems:
        limitation = "无法可靠识别 Java 项目布局。未猜测构建命令。"
    return ProjectLayout(
        systems=systems,
        modules=modules,
        maven_wrapper=maven_wrapper,
        gradle_wrapper=gradle_wrapper,
        limitation=limitation,
        suggested_command=None,
    )
