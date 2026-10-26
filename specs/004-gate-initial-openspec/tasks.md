---

description: "Implementation tasks for the initial OpenSpec quality gate"
---

# Tasks: 从零开始的 OpenSpec 质量门

**Input**: Design documents from `/specs/004-gate-initial-openspec/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 宪章要求 SpecGuard 功能先有失败测试。每个用户故事先写测试并确认失败，再实现代码。

**Organization**: 任务按用户故事分组，使当前规范审核、变更回归、并存选择和报告区分可分别验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可与同阶段其他任务并行，修改不同文件且不依赖未完成任务
- **[Story]**: 对应 `spec.md` 中的用户故事
- 每项任务均包含明确文件路径

## Phase 1: Setup（共享夹具）

**Purpose**: 准备当前规范夹具，不改变现有审核行为。

- [X] T001 Extend fixture materialization for `openspec/specs/<capability>/spec.md` trees in `tests/fixtures/materialize.py`
- [X] T002 [P] Create a current-only fixture with two capabilities, `### Requirement:` entries, scenarios, and no `openspec/changes/` in `tests/fixtures/baseline/current_only/`

---

## Phase 2: Foundational（阻塞性模型）

**Purpose**: 增加所有用户故事共用的对象种类、能力名称和任务可用性字段。

**⚠️ CRITICAL**: 本阶段完成前不得开始用户故事实现。

### Tests

- [X] T003 [P] Add failing model tests that `subject_kind` is `current | change | null`, Spec Kit `subject_kind` must be empty, `subject` must be empty when `subject_kind` is `current`, current `subject_id` is `current`, and `tasks_available` exists on the bundle in `tests/unit/test_artifact_models.py`

### Implementation

- [X] T004 Add `subject_kind: current | change | null` and bundle `tasks_available` to `src/specguard/artifacts/models.py`, rejecting a non-empty `subject` when `subject_kind` is `current`
- [X] T005 Add optional `capability`, report `subject_kind`, `tasks_available`, and schema `1.2` to `src/specguard/models/entities.py`

**Checkpoint**: 新字段可单独验证，选择和解析行为尚未改变。

---

## Phase 3: User Story 1 - 审核一份从零建立的当前规范（Priority: P1）🎯 MVP

**Goal**: 只有当前规范时，不提供变更名也能审核全部需求，且不制造增量语义。

**Independent Test**: 对只有 `openspec/specs/` 的仓库运行审核。报告包含全部需求；范围内有证据和没证据的需求分开；范围外文件不算证据；任务完整性标为不可用；规范与 Git 不变。

### Tests for User Story 1

- [X] T006 [P] [US1] Add failing parser tests for identifier `<capability>:<slug>`, `change_semantics` null, capability name, source line, scenarios, duplicate titles failing before checks, empty body failing, delta-only files failing, and invalid UTF-8 in `tests/unit/test_baseline_parser.py`
- [X] T007 [P] [US1] Add a failing end-to-end test that a current-only repository reviews without a change name, cites evidence only inside the selected revision range, marks out-of-range files as non-evidence, reports tasks unavailable, and leaves `openspec/` and Git unchanged in `tests/integration/test_baseline_review.py`

### Implementation for User Story 1

- [X] T008 [US1] Parse `### Requirement:` entries outside ADDED/MODIFIED/REMOVED from `openspec/specs/<capability>/spec.md` into requirements whose `change_semantics` is null in `src/specguard/openspec/parser.py`
- [X] T009 [US1] Select `subject_id` `current` with `tasks_available` false when only the current specification exists, and load every capability in `src/specguard/artifacts/openspec.py`
- [X] T010 [US1] Accept `artifacts.subject_kind: current` and `--baseline` for the current-only path in `src/specguard/config/models.py` and `src/specguard/cli/main.py`
- [X] T011 [US1] Pass the current-spec bundle through review without treating `tasks_available: false` as zero task gaps passed in `src/specguard/pipeline.py`

**Checkpoint**: 只有当前规范的仓库可以独立完成一次审核。

---

## Phase 4: User Story 2 - 继续审核进行中的变更（Priority: P1）

**Goal**: 没有当前规范时，变更审核的增量语义和选择规则保持不变。

**Independent Test**: 现有单变更样例仍可审核并保留 added/modified/removed。多个变更且未选择时失败。不要求新增字段。

### Tests for User Story 2

- [X] T012 [P] [US2] Add failing tests that a repository with only one change still auto-selects it, and multiple changes without a selection still fail, when `openspec/specs/` is absent in `tests/unit/test_baseline_selection.py`
- [X] T013 [P] [US2] Add a failing regression that normalized change requirements, delta semantics, and task gaps match the pre-baseline behavior in `tests/integration/test_provider_compatibility.py`

### Implementation for User Story 2

- [X] T014 [US2] Keep `subject_kind: change` loading on ADDED/MODIFIED/REMOVED and existing single-change selection when no current specification exists in `src/specguard/artifacts/openspec.py`

**Checkpoint**: 旧的纯变更仓库与增加本功能之前的结论一致。

---

## Phase 5: User Story 3 - 在规范和变更并存时明确选择（Priority: P2）

**Goal**: 两类对象同时存在时必须显式选择，冲突选择在检查前被拒绝。

**Independent Test**: 一个含当前规范和两个变更的仓库中，未选择时退出 `4` 且不写报告；`--baseline` 不加载变更需求；`--change` 不加载其他当前规范需求；两者同时指定时失败。

### Tests for User Story 3

- [X] T015 [P] [US3] Add failing selection tests for coexistence without a choice, explicit current excluding change requirements, and explicit change excluding other current-spec requirements in `tests/unit/test_baseline_selection.py`
- [X] T016 [P] [US3] Add failing CLI and config tests that `--baseline` together with `--change`, or `subject_kind: current` together with a change name, exits `4` before checks in `tests/unit/test_cli.py` and `tests/unit/test_config.py`

### Implementation for User Story 3

- [X] T017 [US3] Fail before checks when current specs and active changes both exist and neither kind was explicitly selected in `src/specguard/artifacts/openspec.py`
- [X] T018 [P] [US3] Reject conflicting `--baseline` and `--change` inputs, and reject `subject_kind: current` when `subject` is non-empty, in `src/specguard/cli/main.py` and `src/specguard/config/models.py`

**Checkpoint**: 未选择或冲突选择不会产生报告，显式选择只加载一种需求来源。

---

## Phase 6: User Story 4 - 在报告中区分审核对象（Priority: P2）

**Goal**: Markdown 和 JSON 都能看出对象是当前规范还是进行中的变更。

**Independent Test**: 两份报告的 `subject_kind`、需求数和缺失工件一致。当前规范报告的 `metadata.change` 与 `artifacts.selected_change` 为空，且不把 `proposal.md` 或变更 `tasks.md` 列为缺失。

### Tests for User Story 4

- [X] T019 [P] [US4] Add failing JSON contract tests for schema `1.2`, `subject_kind`, `tasks_available`, null `metadata.change`, null `artifacts.selected_change`, and retained 1.1 aliases in `tests/unit/test_report_contract.py`
- [X] T020 [P] [US4] Add failing Markdown tests that current-spec reports say 当前规范 and 任务完整性不可用, while change reports say 进行中的变更 and do not list change-only files as missing from the current spec in `tests/unit/test_markdown_report.py`

### Implementation for User Story 4

- [X] T021 [US4] Emit schema `1.2` `subject_kind` and `tasks_available` from the reviewed bundle in `src/specguard/pipeline.py` and `src/specguard/report/json_report.py`
- [X] T022 [P] [US4] Render 当前规范 or 进行中的变更, and render 任务完整性不可用 when `tasks_available` is false, in `src/specguard/report/markdown.py`

**Checkpoint**: 读者无需查看配置就能区分整份规范和一次变更。

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 版本、文档、性能和只读验证。

- [X] T023 [P] Update the package version to `0.3.0` in `pyproject.toml`, `src/specguard/__init__.py`, and `tests/unit/test_install_entry.py`
- [X] T024 [P] Document `--baseline`, `subject_kind`, and the coexistence error in `README.md`, `README.en.md`, `docs/usage.md`, `docs/config-templates.md`, and `docs/report-interpretation.md`
- [X] T025 [P] Add a parse performance test for 100 capability directories and 1000 current-spec requirements completing in under 5 seconds in `tests/integration/test_baseline_performance.py`
- [X] T026 Run the four scenarios in `specs/004-gate-initial-openspec/quickstart.md`, execute the full pytest suite, and record any environment limitation in `specs/004-gate-initial-openspec/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无前置依赖
- **Foundational (Phase 2)**: 依赖 Phase 1，并阻塞所有用户故事
- **User Story 1 (Phase 3)**: 依赖 Foundational
- **User Story 2 (Phase 4)**: 依赖 Foundational；与 US1 共用 OpenSpec 适配器，宜在 US1 的加载路径之后集成
- **User Story 3 (Phase 5)**: 依赖 US1 和 US2 的两种加载路径
- **User Story 4 (Phase 6)**: 依赖 US1 的当前规范结果，并覆盖变更报告
- **Polish (Phase 7)**: 依赖希望交付的全部用户故事

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完成后即可开始，是 MVP
- **User Story 2 (P1)**: 可与 US1 的测试并行编写；实现需避免破坏 US1 的当前规范加载
- **User Story 3 (P2)**: 依赖两种对象都已能加载
- **User Story 4 (P2)**: 依赖当前规范报告数据已经产生

### Within Each User Story

- 测试必须先写并失败，然后再实现
- 解析先于选择，选择先于流水线和报告
- 一个故事完成后再进入下一优先级

### Parallel Opportunities

- T001 与 T002 可并行
- T006 与 T007、T012 与 T013、T015 与 T016、T019 与 T020 可并行
- T017 与 T018、T021 与 T022 修改不同文件，可在各自测试失败后并行
- T023、T024、T025 可并行

---

## Parallel Example: User Story 1

```bash
# 先同时编写并确认失败：
Task: "T006 parser tests in tests/unit/test_baseline_parser.py"
Task: "T007 end-to-end test in tests/integration/test_baseline_review.py"

# 测试失败后按顺序实现：
Task: "T008 parse current requirements in src/specguard/openspec/parser.py"
Task: "T009 load current subject in src/specguard/artifacts/openspec.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1 和 Phase 2
2. 完成 Phase 3 的测试并确认失败
3. 实现当前规范解析、选择和审核
4. 停下来独立验证：不提供变更名也能审核，且无证据需求不是通过

### Incremental Delivery

1. US1 交付从零规范的质量门
2. US2 确认旧变更仓库没有回归
3. US3 关闭两类对象并存时的猜测
4. US4 让报告本身区分对象种类
5. Polish 更新到 v0.3 并跑通 quickstart

### Parallel Team Strategy

1. 共同完成 Setup 与 Foundational
2. 一人实现 US1，另一人编写 US2 回归测试
3. US3 和 US4 在两种加载路径可用后并行

---

## Notes

- [P] 表示不同文件且不依赖未完成任务
- 当前规范与变更并存时不得恢复“唯一变更自动选择”
- `change_semantics` 对当前规范必须保持 `null`
- 范围外文件不得成为证据
- 每个故事都可以在检查点单独验证

## Phase 8: Convergence

- [X] T027 CRITICAL: Correct current-spec scenario `source_line` to the real file line in `src/specguard/openspec/parser.py` per Constitution II (contradicts)
- [X] T028 Reject a current-spec file whose resolved path leaves the repository with a usage error before checks in `src/specguard/openspec/parser.py` and `src/specguard/artifacts/openspec.py` per data-model: path validation (partial)
- [X] T029 When the selected revision range contains no code or tests, complete the current-spec review, mark every requirement insufficient, and state that the range has no verifiable evidence in `src/specguard/pipeline.py` and `src/specguard/report/markdown.py` per spec: empty revision range (partial)

## Phase 9: Convergence

- [X] T030 CRITICAL: Correct OpenSpec change scenario `source_line` to the real file line in `parse_requirements` in `src/specguard/openspec/parser.py` per Constitution II (contradicts)
