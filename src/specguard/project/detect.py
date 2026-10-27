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


def coverage_for(repo: Path, changed_paths: list[str], checks_enabled: bool):
    from specguard.models.entities import ModuleCoverage

    layout = detect_project(repo)
    if layout.limitation:
        return ModuleCoverage(execution="unrecognized")
    owners: list[str] = []
    for path in changed_paths:
        match = "." if "." in layout.modules else None
        for module in layout.modules:
            if module == ".":
                continue
            if path == module or path.startswith(module + "/"):
                if match in {None, "."} or len(module) > len(match):
                    match = module
        if match and match not in owners:
            owners.append(match)
    owners.sort()
    if not checks_enabled:
        return ModuleCoverage(changed_modules=owners, execution="not_configured")
    uncovered = owners if len(owners) > 1 else []
    return ModuleCoverage(
        changed_modules=owners,
        execution="repository",
        not_separately_covered=uncovered,
    )


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
