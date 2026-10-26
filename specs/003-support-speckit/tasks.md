---

description: "Implementation tasks for Spec Kit artifact support"
---

# Tasks: Spec Kit 工件支持

**Input**: Design documents from `/specs/003-support-speckit/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 宪章要求 SpecGuard 功能先有失败测试；每个用户故事均先完成并确认对应测试失败，再实现代码。

**Organization**: 任务按用户故事分组，使 Spec Kit 审核、对象选择、OpenSpec 兼容和报告契约可分别验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可与同阶段其他任务并行，修改不同文件且不依赖未完成任务
- **[Story]**: 对应 `spec.md` 中的用户故事
- 每项任务均包含明确文件路径

## Phase 1: Setup（共享结构）

**Purpose**: 建立工件提供方包和 Spec Kit 测试夹具目录，不改变现有运行行为。

- [ ] T001 Create the artifact provider package exports in `src/specguard/artifacts/__init__.py`
- [ ] T002 [P] Extend fixture materialization helpers for `.specify/` and `specs/<feature>/` trees in `tests/fixtures/materialize.py`

---

## Phase 2: Foundational（阻塞性基础）

**Purpose**: 建立所有用户故事共用的中立模型、provider 协议和配置入口。

**⚠️ CRITICAL**: 本阶段完成前不得开始用户故事实现。

### Tests

- [ ] T003 [P] Add failing model tests covering `ArtifactProviderConfig`, `ArtifactSubject`, `ArtifactBundle`, and `ContextDocument` constraints from `data-model.md` in `tests/unit/test_artifact_models.py`
- [ ] T004 [P] Add failing provider contract tests for read-only `discover/select/validate/load` behavior in `tests/unit/test_artifact_provider.py`
- [ ] T005 [P] Add failing configuration tests for `artifacts.provider` values `openspec|speckit|auto`, repository-relative `root`, optional `subject`, and default `include_context: true` in `tests/unit/test_config.py`

### Implementation

- [ ] T006 Implement `ArtifactProviderConfig`, `ArtifactSubject`, `ArtifactBundle`, and `ContextDocument` with repository-bound path and selection-source validation in `src/specguard/artifacts/models.py`
- [ ] T007 Implement the read-only `ArtifactProvider` protocol and provider registry without format-specific directory rules in `src/specguard/artifacts/provider.py`
- [ ] T008 Add optional `artifacts` configuration while retaining the existing required semantics of version 1 configurations in `src/specguard/config/models.py`

**Checkpoint**: 中立模型与 provider 边界可单独测试，现有 OpenSpec 流水线尚未切换。

---

## Phase 3: User Story 1 - 审核一个 Spec Kit 功能（Priority: P1）🎯 MVP

**Goal**: 显式选择一个 Spec Kit 功能，解析 `FR-*`、`T*` 和上下文工件，并用现有证据流水线生成审核结果。

**Independent Test**: 对含 `spec.md`、`plan.md` 和 `tasks.md` 的样例仓库显式运行审核；报告列出全部原始需求/任务 ID、真实来源行和证据状态，Spec Kit 需求的增量语义为 `null`。

### Tests（先写并确认失败）

- [ ] T009 [P] [US1] Create a standard Spec Kit fixture with `FR-*`, acceptance scenarios, `[X] T* [P] [USn]`, and optional context documents in `tests/fixtures/speckit/standard/`
- [ ] T010 [P] [US1] Add failing parser tests for requirement ID/body/source line/user story/priority/scenarios, task completion/parallel/story metadata, CRLF, Chinese text, duplicate IDs, and template placeholders in `tests/unit/test_speckit_parser.py`
- [ ] T011 [P] [US1] Add failing provider load tests proving `spec.md|plan.md|tasks.md` completeness and optional context classification without treating context as evidence in `tests/unit/test_artifact_provider.py`
- [ ] T012 [P] [US1] Add a failing end-to-end test for explicit Spec Kit configuration, traceability, task gaps, and unchanged artifact files in `tests/integration/test_speckit_review.py`

### Implementation

- [ ] T013 [P] [US1] Extend `Requirement.change_semantics` to `added|modified|removed|null` and add optional `user_story_id` and `priority`; add `parallel` and optional `user_story_id` to `TaskItem` in `src/specguard/models/entities.py`
- [ ] T014 [US1] Implement Spec Kit `FR-*` requirement and numbered Given/When/Then scenario parsing with duplicate/template validation in `src/specguard/artifacts/speckit.py`
- [ ] T015 [US1] Implement Spec Kit `T*` task parsing, completion markers, `[P]`, `[USn]`, source lines, and duplicate validation in `src/specguard/artifacts/speckit.py`
- [ ] T016 [US1] Load `plan.md`, `research.md`, `data-model.md`, `contracts/**`, `quickstart.md`, and `checklists/**` as bounded `ContextDocument` entries in `src/specguard/artifacts/speckit.py`
- [ ] T017 [US1] Implement explicit `speckit` provider selection and loading into an `ArtifactBundle` in `src/specguard/artifacts/provider.py`
- [ ] T018 [US1] Refactor review orchestration to consume `ArtifactBundle` while preserving existing traceability, task integrity, test adequacy, risk, and policy stages in `src/specguard/pipeline.py`

**Checkpoint**: 显式配置的单个 Spec Kit 功能可独立审核；这是建议的 MVP 边界。

---

## Phase 4: User Story 2 - 可靠选择 Spec Kit 审核对象（Priority: P1）

**Goal**: 按显式 CLI、显式配置、`.specify/feature.json` 的顺序选择功能，并在歧义或非法路径时于检查前失败。

**Independent Test**: 在双功能夹具上分别验证 CLI、配置、状态文件、无效 JSON、越界路径、缺少 `spec.md` 和未选择；失败场景不运行检查、不调用模型、不写报告。

### Tests（先写并确认失败）

- [ ] T019 [P] [US2] Create multiple-feature, malformed-state, missing-spec, and symlink/path-escape fixtures in `tests/fixtures/speckit/selection/`
- [ ] T020 [P] [US2] Add failing selection tests for CLI > config > feature state precedence, no Git-branch inference, ambiguity, malformed JSON, non-string state, missing directories, and repository escape in `tests/unit/test_speckit_discovery.py`
- [ ] T021 [P] [US2] Add failing CLI tests for `--subject`, configuration override, and `help/version` avoiding artifact discovery in `tests/unit/test_cli.py`
- [ ] T022 [P] [US2] Add failing integration tests proving invalid selection exits `4` before checks/network/report writes and leaves `.specify/feature.json` unchanged in `tests/integration/test_speckit_selection.py`

### Implementation

- [ ] T023 [US2] Implement read-only `.specify/feature.json` parsing, explicit-selection precedence, ambiguity handling, repository containment, symlink escape rejection, and required `spec.md` validation in `src/specguard/artifacts/speckit.py`
- [ ] T024 [US2] Add `--subject` handling and pass the neutral selection to configuration/pipeline without running discovery for `help` or `version` in `src/specguard/cli/main.py`
- [ ] T025 [US2] Move provider selection and validation ahead of deterministic checks and assisted-review setup, mapping selection failures to usage exit code `4`, in `src/specguard/pipeline.py`

**Checkpoint**: 多功能 Spec Kit 仓库的审核对象选择可审计，所有选择错误均安全地提前失败。

---

## Phase 5: User Story 3 - 保持 OpenSpec 用户兼容（Priority: P1）

**Goal**: 把现有 OpenSpec 行为包装为 provider，并保持版本 1 配置、`--change`、增量语义和报告结论。

**Independent Test**: 使用现有单变更和多变更 OpenSpec 夹具运行回归；旧配置无需修改，同时存在两种工件时显式 OpenSpec 只加载 OpenSpec，冲突配置在检查前失败。

### Tests（先写并确认失败）

- [ ] T026 [P] [US3] Add failing OpenSpec provider contract tests covering discovery, explicit/multiple-change selection, delta semantics, tasks, main specs, and missing artifacts in `tests/unit/test_openspec_provider.py`
- [ ] T027 [P] [US3] Add failing compatibility tests for legacy `openspec`-only configuration, matching dual configuration, conflicting root/subject, and `artifacts.provider != openspec` conflicts in `tests/unit/test_config.py`
- [ ] T028 [P] [US3] Add failing CLI compatibility tests proving `--change` remains OpenSpec-only and conflicts with incompatible `--subject` values/providers in `tests/unit/test_cli.py`
- [ ] T029 [P] [US3] Add an end-to-end regression test comparing normalized OpenSpec requirements/tasks/findings with the pre-provider behavior in `tests/integration/test_provider_compatibility.py`

### Implementation

- [ ] T030 [US3] Implement the OpenSpec adapter by reusing existing discovery/parser behavior and emitting `ArtifactBundle` without changing delta semantics in `src/specguard/artifacts/openspec.py`
- [ ] T031 [US3] Add legacy `openspec`-to-provider mapping, matching dual-config acceptance, and conflicting dual-config rejection in `src/specguard/config/models.py`
- [ ] T032 [US3] Preserve `--change` as an OpenSpec-only compatibility alias and reject conflicting neutral selections in `src/specguard/cli/main.py`
- [ ] T033 [US3] Remove direct OpenSpec discovery/parser imports from the core orchestration and route both providers through the registry in `src/specguard/pipeline.py`

**Checkpoint**: OpenSpec 与 Spec Kit 均经同一中立边界运行，现有 OpenSpec 用户无需迁移配置。

---

## Phase 6: User Story 4 - 在报告中区分工件来源（Priority: P2）

**Goal**: Markdown 与 JSON 明确记录 provider、subject 和选择来源，报告 schema 更新为 1.1 并保留兼容别名。

**Independent Test**: 分别生成 OpenSpec 与 Spec Kit 报告；两种格式的 provider、subject、选择来源、需求数、任务缺口及工件清单一致，旧字段继续存在。

### Tests（先写并确认失败）

- [ ] T034 [P] [US4] Add failing entity/JSON contract tests for schema `1.1`, `artifact_provider`, `subject_id`, `selection_source`, context inventory, nullable Spec Kit semantics, and deprecated aliases in `tests/unit/test_report_contract.py`
- [ ] T035 [P] [US4] Add failing Markdown tests for provider, subject, selection source, provider-specific missing artifacts, and no OpenSpec-only missing labels in Spec Kit reports in `tests/unit/test_markdown_report.py`
- [ ] T036 [P] [US4] Add failing cross-format integration assertions for matching counts and artifact metadata in `tests/integration/test_speckit_review.py`

### Implementation

- [ ] T037 [US4] Upgrade `ReviewReport.schema_version` to `1.1` and add neutral provider/subject/selection/context fields while retaining deprecated `metadata.change` and `artifacts.selected_change` aliases in `src/specguard/models/entities.py`
- [ ] T038 [P] [US4] Render schema 1.1 neutral artifact metadata and compatibility aliases in `src/specguard/report/json_report.py`
- [ ] T039 [P] [US4] Render provider, subject, selection source, and provider-specific artifact completeness in `src/specguard/report/markdown.py`

**Checkpoint**: 人工读者和程序消费者都能区分工件来源，且有明确报告版本迁移路径。

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 完成辅助审查安全、版本发布、文档、性能与全量验证。

- [ ] T040 [P] Add failing assisted-review tests proving Spec Kit context is bounded, redacted, treated as untrusted, and never upgrades evidence by itself in `tests/unit/test_assisted_speckit_context.py`
- [ ] T041 Add bounded Spec Kit `ContextDocument` content to redaction/truncation flow without changing hypothesis policy in `src/specguard/review/assisted.py`
- [ ] T042 [P] Update package version to `0.2.0` and add a version assertion in `src/specguard/__init__.py` and `tests/unit/test_install_entry.py`
- [ ] T043 [P] Document provider selection, `--subject`, legacy `--change`, ambiguity errors, and v0.2 migration in `README.md`, `README.en.md`, `docs/usage.md`, `docs/config-templates.md`, and `docs/report-interpretation.md`
- [ ] T044 [P] Add a discovery/parsing performance test for 100 feature directories, 1000 requirements, and 5000 tasks under 5 seconds in `tests/integration/test_speckit_performance.py`
- [ ] T045 Run the four scenarios in `specs/003-support-speckit/quickstart.md`, execute the full `pytest` suite, and record any environment limitations in `specs/003-support-speckit/quickstart.md`
- [ ] T046 Verify with a repository snapshot test that Spec Kit artifacts, `.specify/feature.json`, Git index, and commit history remain unchanged after review in `tests/integration/test_readonly_repository.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: 无依赖。
- **Phase 2 Foundational**: 依赖 Phase 1；阻塞所有用户故事。
- **US1（Phase 3）**: 依赖 Phase 2；建立 Spec Kit MVP。
- **US2（Phase 4）**: 依赖 Phase 2 的中立模型；端到端验证依赖 US1 provider 加载完成。
- **US3（Phase 5）**: 依赖 Phase 2，可与 US1/US2 的格式专属工作并行；最终流水线切换需协调 T018/T033。
- **US4（Phase 6）**: 依赖 US1 和 US3 都能产生规范化工件包。
- **Polish（Phase 7）**: 依赖计划交付的用户故事完成；性能、文档和部分测试可提前准备。

### User Story Dependencies

- **US1（P1）**: Foundation → Spec Kit 显式审核；MVP。
- **US2（P1）**: Foundation → 选择逻辑；单元实现可独立，端到端测试复用 US1。
- **US3（P1）**: Foundation → OpenSpec provider；可与 US1 并行。
- **US4（P2）**: US1 + US3 → 统一报告契约。

### Within Each User Story

- 测试任务必须先完成并确认失败。
- 模型和解析器先于 provider 加载。
- provider 加载先于流水线集成。
- 单元与契约测试通过后再运行故事的独立集成测试。
- 不得通过删除测试、弱化断言或把错误状态改为通过来完成任务。

### Parallel Opportunities

- T002 可与 T001 并行。
- T003、T004、T005 修改不同测试文件，可并行。
- US1 的 T009、T010、T011、T012 可并行准备。
- US2 的 T019、T020、T021、T022 可并行准备。
- US3 的 T026、T027、T028、T029 可并行准备。
- 基础完成后，US1 的格式解析与 US3 的 OpenSpec 适配可由不同开发者并行。
- US4 的 JSON 与 Markdown 渲染 T038、T039 可并行。
- T040、T042、T043、T044 修改不同文件，可并行。

---

## Parallel Example: User Story 1

```text
Task T009: 创建标准 Spec Kit 夹具
Task T010: 编写 Spec Kit 解析失败测试
Task T011: 编写 provider 加载失败测试
Task T012: 编写显式审核端到端失败测试
```

## Parallel Example: User Story 3

```text
Task T026: 编写 OpenSpec provider 契约测试
Task T027: 编写旧配置兼容测试
Task T028: 编写 --change CLI 兼容测试
Task T029: 编写 OpenSpec 端到端回归测试
```

---

## Implementation Strategy

### MVP First（US1）

1. 完成 Phase 1 与 Phase 2。
2. 完成 US1 的失败测试。
3. 实现显式配置的 Spec Kit 解析与审核。
4. 停止并按 US1 Independent Test 独立验证。
5. MVP 不包含状态文件自动选择、OpenSpec provider 重构或报告 1.1 发布。

### Incremental Delivery

1. Foundation → 中立工件模型和 provider 契约。
2. US1 → 显式 Spec Kit 审核 MVP。
3. US2 → 安全、可审计的活动功能选择。
4. US3 → OpenSpec 兼容与统一流水线。
5. US4 → 报告 1.1 和程序消费契约。
6. Polish → 辅助审查安全、v0.2 发布、文档、性能和只读证明。

### Parallel Team Strategy

1. 团队共同完成 Setup 与 Foundational。
2. Foundation 完成后：
   - Developer A：US1 Spec Kit 解析与加载。
   - Developer B：US2 选择与路径安全。
   - Developer C：US3 OpenSpec 适配与兼容。
3. 三个 P1 故事完成后共同完成 US4 报告契约与全量回归。

---

## Notes

- `[P]` 表示修改不同文件且无未完成依赖，不代表同文件任务可同时提交。
- `[USn]` 与规格中的用户故事一一对应。
- 每个故事先测试后实现，并在 checkpoint 独立验证。
- `ContextDocument` 只提供上下文，不得直接成为实现完成证据。
- Spec Kit 支持属于 v0.2；v0.1 仍遵守宪章的 OpenSpec-only 范围。
