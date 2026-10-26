from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from specguard.models.entities import MainRequirement, Requirement, TaskItem, UserStory

ProviderName = Literal["openspec", "speckit", "auto"]
ConcreteProviderName = Literal["openspec", "speckit"]
SelectionSource = Literal["cli", "config", "feature_state", "legacy_config"]
SubjectKind = Literal["current", "change", "feature"]
ContextKind = Literal[
    "plan",
    "research",
    "data_model",
    "contract",
    "quickstart",
    "checklist",
    "proposal",
    "design",
    "main_spec",
]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _relative_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("路径必须是仓库内相对路径")
    normalized = str(path)
    if normalized in {"", "."}:
        raise ValueError("路径不能为空")
    return normalized


class ArtifactProviderConfig(_Strict):
    provider: ProviderName = "openspec"
    root: str | None = None
    subject: str | None = None
    subject_kind: Literal["current", "change"] | None = None
    include_context: bool = True

    @model_validator(mode="after")
    def provider_defaults(self) -> "ArtifactProviderConfig":
        if self.root is None:
            self.root = "specs" if self.provider == "speckit" else "openspec"
        if self.provider == "speckit" and self.subject_kind is not None:
            raise ValueError("Spec Kit 的 subject_kind 必须为空")
        if self.subject_kind == "current" and self.subject:
            raise ValueError("subject_kind 为 current 时 subject 必须为空")
        return self

    @field_validator("root")
    @classmethod
    def relative_root(cls, value: str | None) -> str | None:
        return None if value is None else _relative_path(value)


class ArtifactSubject(_Strict):
    provider: ConcreteProviderName
    subject_id: str
    directory: Path
    selection_source: SelectionSource
    subject_kind: SubjectKind | None = None

    @field_validator("subject_id")
    @classmethod
    def nonempty_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("审核对象不能为空")
        return value

    @field_validator("directory")
    @classmethod
    def absolute_directory(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("审核对象目录必须是绝对路径")
        return value


class ContextDocument(_Strict):
    kind: ContextKind
    path: str
    title: str | None = None
    content: str = Field(default="", max_length=50_000)

    @field_validator("path")
    @classmethod
    def relative_document_path(cls, value: str) -> str:
        return _relative_path(value)


class ArtifactBundle(_Strict):
    subject: ArtifactSubject
    found: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    user_stories: list[UserStory] = Field(default_factory=list)
    tasks: list[TaskItem] = Field(default_factory=list)
    context_documents: list[ContextDocument] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    tasks_available: bool = True
    main_specs: list[str] = Field(default_factory=list)
    main_requirements: list[MainRequirement] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_identifiers(self) -> "ArtifactBundle":
        for label, values in (
            ("需求", [item.identifier for item in self.requirements]),
            ("任务", [item.identifier for item in self.tasks]),
        ):
            duplicates = sorted({item for item in values if values.count(item) > 1})
            if duplicates:
                raise ValueError(f"{label} ID 重复: {', '.join(duplicates)}")
        return self
