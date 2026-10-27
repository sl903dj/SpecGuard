from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from specguard.artifacts.models import ArtifactProviderConfig
from specguard.config.allowlist import command_allowed


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectConfig(_Strict):
    name: str = "project"
    root: str = "."


class OpenSpecConfig(_Strict):
    root: str = "openspec"
    change: str | None = None
    include_main_specs: bool = True
    require_change_selection: bool = True
    validate_before_review: bool = False


class GitConfig(_Strict):
    base: str
    target: str = "HEAD"
    include_worktree: bool = False
    fail_on_uncommitted_changes: bool = True
    evidence_scope: Literal["range", "target_tree"] = "range"


class Dimensions(_Strict):
    requirements: bool = True
    business_logic: bool = True
    test_adequacy: bool = True
    regression: bool = True


class SeverityThresholds(_Strict):
    block_on: list[str] = Field(default_factory=lambda: ["critical", "high"])


class ReviewConfig(_Strict):
    mode: Literal["static", "assisted"] = "static"
    policy: Literal["advisory", "strict"] = "advisory"
    dimensions: Dimensions = Field(default_factory=Dimensions)
    severity_thresholds: SeverityThresholds = Field(default_factory=SeverityThresholds)
    llm_findings_block: bool = False

    @field_validator("llm_findings_block")
    @classmethod
    def only_false(cls, value: bool) -> bool:
        if value:
            raise ValueError("review.llm_findings_block 只接受 false")
        return value


class CheckSpec(_Strict):
    enabled: bool = False
    required: bool = False
    command: str | None = None
    timeout_seconds: int = 600

    @field_validator("timeout_seconds")
    @classmethod
    def positive_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("超时必须为正整数")
        return value

    @field_validator("command")
    @classmethod
    def allowlisted(cls, value: str | None) -> str | None:
        if value is not None and not command_allowed(value):
            raise ValueError("命令不在允许列表中")
        return value


class ChecksConfig(_Strict):
    build: CheckSpec = Field(default_factory=CheckSpec)
    tests: CheckSpec = Field(default_factory=CheckSpec)
    checkstyle: CheckSpec = Field(default_factory=CheckSpec)
    spotbugs: CheckSpec = Field(default_factory=CheckSpec)
    pmd: CheckSpec = Field(default_factory=CheckSpec)
    jacoco: CheckSpec = Field(default_factory=CheckSpec)
    archunit: CheckSpec = Field(default_factory=CheckSpec)
    openspec_validate: CheckSpec = Field(default_factory=CheckSpec)


class LlmConfig(_Strict):
    enabled: bool = False
    provider: str = "internal-openai-compatible"
    base_url: str | None = None
    model: str | None = None
    api_key_env: str = "SPECGUARD_API_KEY"
    timeout_seconds: int = 120
    max_retries: int = 1
    max_context_chars: int = 50000
    external_fallback: bool = False

    @field_validator("timeout_seconds", "max_retries", "max_context_chars")
    @classmethod
    def positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("必须为正数")
        return value

    @field_validator("external_fallback")
    @classmethod
    def no_fallback(cls, value: bool) -> bool:
        if value:
            raise ValueError("llm.external_fallback 只接受 false")
        return value

    @field_validator("provider")
    @classmethod
    def internal_only(cls, value: str) -> str:
        if value != "internal-openai-compatible":
            raise ValueError("llm.provider 只接受 internal-openai-compatible")
        return value


class SecurityConfig(_Strict):
    redact_secrets: bool = True
    external_network: bool = False
    max_command_output_bytes: int = 200000
    isolate_builds: bool = True

    @field_validator("max_command_output_bytes")
    @classmethod
    def positive_bytes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_command_output_bytes 必须为正数")
        return value


class ReportConfig(_Strict):
    formats: list[Literal["markdown", "json"]] = Field(
        default_factory=lambda: ["markdown", "json"]
    )
    output_dir: str = ".specguard/reports"
    include_source_snippets: bool = False

    @field_validator("formats")
    @classmethod
    def both_formats(cls, value: list[str]) -> list[str]:
        if set(value) != {"markdown", "json"}:
            raise ValueError("report.formats 必须同时包含 markdown 和 json")
        return value


class SpecGuardConfig(_Strict):
    version: Literal[1]
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    openspec: OpenSpecConfig = Field(default_factory=OpenSpecConfig)
    artifacts: ArtifactProviderConfig | None = None
    git: GitConfig
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    checks: ChecksConfig = Field(default_factory=ChecksConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)

    @model_validator(mode="before")
    @classmethod
    def compatible_artifact_configuration(cls, value):
        if not isinstance(value, dict) or "artifacts" not in value or "openspec" not in value:
            return value
        artifacts = value.get("artifacts")
        legacy = value.get("openspec")
        if not isinstance(artifacts, dict) or not isinstance(legacy, dict):
            return value
        provider = artifacts.get("provider", "openspec")
        artifact_root = artifacts.get("root", "openspec" if provider != "speckit" else "specs")
        legacy_root = legacy.get("root", "openspec")
        if provider != "openspec":
            raise ValueError("artifacts.provider 与旧 openspec 配置冲突")
        if artifact_root != legacy_root:
            raise ValueError("artifacts.root 与 openspec.root 冲突")
        if artifacts.get("subject") != legacy.get("change"):
            raise ValueError("artifacts.subject 与 openspec.change 冲突")
        return value

    @model_validator(mode="after")
    def assisted_needs_provider(self) -> "SpecGuardConfig":
        if self.review.mode == "assisted" and (not self.llm.enabled or not self.llm.base_url):
            raise ValueError("assisted 模式必须启用 llm 并提供 llm.base_url")
        if self.llm.enabled and not self.llm.base_url:
            raise ValueError("llm.base_url 不能为空")
        from specguard.llm.client import is_internal_endpoint

        if (
            not self.security.external_network
            and self.llm.base_url
            and not is_internal_endpoint(self.llm.base_url)
        ):
            raise ValueError("external_network 为 false 时 llm.base_url 必须是内网或回环地址")
        return self

    def artifact_provider_config(self) -> ArtifactProviderConfig:
        if self.artifacts is not None:
            return self.artifacts
        return ArtifactProviderConfig(
            provider="openspec",
            root=self.openspec.root,
            subject=self.openspec.change,
            subject_kind="change" if self.openspec.change else None,
            include_context=True,
        )
