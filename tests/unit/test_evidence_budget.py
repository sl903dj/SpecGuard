import time

from specguard.models.entities import ChangedFile, Requirement
from specguard.review.traceability import link_requirements


def test_requirement_linkage_stays_within_five_seconds() -> None:
    requirements = [
        Requirement(
            identifier=f"order:requirement-{index}",
            title=f"Requirement {index}",
            change_semantics=None,
            source_file="openspec/specs/order/spec.md",
            source_line=index + 1,
            body="系统必须保留这条需求的原始说明。",
        )
        for index in range(1000)
    ]
    files = [
        ChangedFile(path=f"src/main/java/File{index}.java", change_type="modified") for index in range(2000)
    ]

    def read_text(path: str) -> str:
        return "class File {}\n"

    started = time.perf_counter()
    link_requirements(requirements, files, read_text)
    elapsed = time.perf_counter() - started
    assert elapsed < 5
