from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from specguard.models.status import CheckStatus, ReviewStatus

DISCLAIMER = "缺少测试证据不等于代码一定有错；静态或自动检查未发现问题也不等于代码安全。"

ChangeType = Literal["added", "modified", "deleted", "renamed"]
Semantics = Literal["added", "modified", "removed"]
EvidenceKind = Literal["direct", "inferred", "insufficient"]
Claim = Literal["confirmed", "hypothesis", "insufficient"]
Support = Literal["code", "test", "both", "none"]
Severity = Literal["critical", "high", "medium", "low", "info"]
Category = Literal[
    "requirements",
    "task_integrity",
    "business_logic",
    "test_adequacy",
    "regression",
]
RiskClass = Literal[
    "boundary",
    "exception",
    "null_empty",
    "transaction",
    "concurrency",
    "authorization",
    "compatibility",
    "persisted_data",
    "dependency_config",
]
EvidenceScopeName = Literal["range", "target_tree"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LineRange(_Model):
    start: int
    end: int

    @model_validator(mode="after")
    def real_lines(self) -> "LineRange":
        if self.start <= 0 or self.end <= 0:
            raise ValueError("不得伪造行号")
        return self


class ChangedFile(_Model):
    path: str
    previous_path: str | None = None
    change_type: ChangeType
    line_ranges: list[LineRange] = Field(default_factory=list)
    committed: bool = True


class Location(_Model):
    file: str
    line_start: int
    line_end: int

    @model_validator(mode="after")
    def real_lines(self) -> "Location":
        if self.line_start <= 0 or self.line_end <= 0:
            raise ValueError("不得伪造行号")
        return self


class Evidence(_Model):
    status: EvidenceKind
    requirement_id: str | None = None
    task_id: str | None = None
    file: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    check_id: str | None = None
    note: str = ""

    @model_validator(mode="after")
    def note_when_uncertain(self) -> "Evidence":
        if self.status in {"inferred", "insufficient"} and not self.note:
            raise ValueError("推断和证据不足必须说明原因")
        if self.line_start == 0 or self.line_end == 0:
            raise ValueError("不得伪造行号")
        return self


class Scenario(_Model):
    name: str
    source_line: int
    body: str = ""


class UserStory(_Model):
    identifier: str
    title: str
    priority: str | None = None
    scenarios: list[Scenario] = Field(default_factory=list)
    source_line: int


class Requirement(_Model):
    identifier: str
    title: str
    change_semantics: Semantics | None
    capability: str | None = None
    user_story_id: str | None = None
    priority: str | None = None
    scenarios: list[Scenario] = Field(default_factory=list)
    source_file: str
    source_line: int
    body: str = ""
    ambiguous: bool = False
    ambiguity_reason: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class TaskItem(_Model):
    identifier: str
    text: str
    marked_complete: bool = False
    parallel: bool = False
    user_story_id: str | None = None
    source_file: str
    source_line: int
    support: Support = "none"
    evidence: list[Evidence] = Field(default_factory=list)


class CheckResult(_Model):
    check_id: str
    required: bool
    status: CheckStatus
    command: str | None = None
    duration_seconds: float | None = None
    exit_code: int | None = None
    diagnostic: str | None = None
    tool_version: str | None = None

    def rewrite(self, proposed: CheckStatus) -> None:
        from specguard.models.status import rewrite_status

        self.status = rewrite_status(self.status, proposed)


class Finding(_Model):
    finding_id: str = ""
    category: Category
    severity: Severity
    summary: str
    failure_path: str | None = None
    evidence_status: Claim
    origin: str
    risk_class: RiskClass | None = None
    location: Location | None = None
    related_requirement_ids: list[str] = Field(default_factory=list)
    related_task_ids: list[str] = Field(default_factory=list)
    duplicate_group: str | None = None
    attributes_cause: bool = False

    def is_defect(self) -> bool:
        return (
            self.evidence_status == "confirmed"
            and bool(self.failure_path)
            and self.location is not None
        )


class PolicyView(_Model):
    mode: Literal["advisory", "strict"]
    blocked: bool
    reasons: list[str] = Field(default_factory=list)


class RedactionNote(_Model):
    category: str
    count: int


class ScenarioAssessment(_Model):
    requirement_id: str
    scenario_name: str | None = None
    status: Literal["supported", "gap", "unavailable"]
    test_file: str | None = None
    test_line: int | None = None
    note: str = ""

    @model_validator(mode="after")
    def support_needs_location(self) -> "ScenarioAssessment":
        if self.status == "supported":
            if not self.test_file or self.test_line is None or self.test_line <= 0:
                raise ValueError("已有测试支撑必须给出测试位置")
        elif not self.note:
            raise ValueError("缺口和不可用必须说明原因")
        return self


class ConsistencyItem(_Model):
    capability: str
    current_requirement_id: str
    current_file: str
    current_line: int
    change_requirement_id: str | None = None
    change_file: str
    change_line: int
    status: Literal["conflict", "human_review"]
    summary: str

    @model_validator(mode="after")
    def real_sources(self) -> "ConsistencyItem":
        if self.current_line <= 0 or self.change_line <= 0:
            raise ValueError("不得伪造行号")
        return self


class CalibrationView(_Model):
    status: Literal["incomplete", "complete"] = "incomplete"
    completed_review_count: int = 0
    rejected_complete_mark: bool = False
    notes: list[str] = Field(default_factory=list)


class RiskDisposition(_Model):
    risk_class: RiskClass
    disposition: Literal["finding", "missing_context"]


class ModuleCoverage(_Model):
    changed_modules: list[str] = Field(default_factory=list)
    execution: Literal["repository", "unrecognized", "not_configured"] = "not_configured"
    not_separately_covered: list[str] = Field(default_factory=list)


class Metadata(_Model):
    tool_version: str
    config_version: int
    repository_root: str
    base: str
    target: str
    head_sha: str
    change: str | None
    artifact_provider: Literal["openspec", "speckit"] | None = None
    subject_id: str | None = None
    selection_source: Literal["cli", "config", "feature_state", "legacy_config"] | None = None
    subject_kind: Literal["current", "change", "feature"] | None = None
    tasks_available: bool = True
    evidence_scope: EvidenceScopeName = "range"
    calibration: CalibrationView = Field(default_factory=CalibrationView)
    module_coverage: ModuleCoverage = Field(default_factory=ModuleCoverage)
    risk_dispositions: list[RiskDisposition] = Field(default_factory=list)
    started_at: str
    finished_at: str
    limitations: list[str] = Field(default_factory=list)
    output_paths: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    redactions: list[RedactionNote] = Field(default_factory=list)
    service_id: str | None = None
    model_id: str | None = None
    source_snippets: list[str] = Field(default_factory=list)


class Summary(_Model):
    needs_human_review: bool
    direct_count: int = 0
    inferred_count: int = 0
    insufficient_count: int = 0
    task_gap_count: int = 0
    highest_risks: list[str] = Field(default_factory=list)
    reliable_checks: list[str] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER
    coverage_percent: float | None = None


class MainRequirement(_Model):
    title: str
    body: str
    source_file: str
    source_line: int


class ArtifactContextEntry(_Model):
    kind: Literal[
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
    path: str


class ArtifactReport(_Model):
    available: bool = False
    provider: Literal["openspec", "speckit"] | None = None
    subject_id: str | None = None
    selection_source: Literal["cli", "config", "feature_state", "legacy_config"] | None = None
    subject_kind: Literal["current", "change", "feature"] | None = None
    tasks_available: bool = True
    found: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    context_documents: list[ArtifactContextEntry] = Field(default_factory=list)
    selected_change: str | None = None
    main_specs: list[str] = Field(default_factory=list)
    main_requirements: list[MainRequirement] = Field(default_factory=list)


class ReviewReport(_Model):
    schema_version: Literal["1.3"] = "1.3"
    review_status: ReviewStatus
    policy: PolicyView
    metadata: Metadata
    summary: Summary
    changed_files: list[ChangedFile] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    tasks: list[TaskItem] = Field(default_factory=list)
    checks: list[CheckResult] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    conflicts: list[list[str]] = Field(default_factory=list)
    scenario_assessments: list[ScenarioAssessment] = Field(default_factory=list)
    consistency_items: list[ConsistencyItem] = Field(default_factory=list)
    artifacts: ArtifactReport = Field(default_factory=ArtifactReport)
