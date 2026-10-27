---

description: "Implementation tasks for closing SpecGuard review evidence gaps"
---

# Tasks: 补齐质量门的证据与对照能力

**Input**: Design documents from `/specs/005-close-review-gaps/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 宪章要求 SpecGuard 功能先有失败测试。每个用户故事先写测试并确认失败，再实现代码。

**Organization**: 任务按用户故事分组。需求证据、规范对照、历史对照、风险类别、证据范围和模块覆盖可以分别验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可与同阶段、同一小节内其他标了 [P] 的任务并行，修改不同文件且不依赖未完成任务
- **[Story]**: 对应 `spec.md` 中的用户故事
- 每项任务均包含明确文件路径

## Phase 1: Setup（共享夹具）

**Purpose**: 准备六个场景共用的临时仓库材料，不改变现有审核行为。

- [X] T001 [P] Add a git fixture builder that creates an OpenSpec current spec, one in-progress change, an in-range implementation file, an out-of-range file, a scenario test, and a trivial-assertion test in `tests/fixtures/review_gaps/materialize.py`
- [X] T002 [P] Add calibration samples `incomplete.json`, `false_complete.json`, `complete.json`, and `secret.json` under `tests/fixtures/review_gaps/calibration/`

---

## Phase 2: Foundational（阻塞性模型）

**Purpose**: 增加所有用户故事共用的报告字段和证据范围配置。默认值不得改变现有审核结论。

**⚠️ CRITICAL**: 本阶段完成前不得开始用户故事实现。

### Tests

- [X] T003 Add failing model tests that `schema_version` is `1.3`, `Scenario.body` defaults to `""`, `evidence_scope` defaults to `range`, `calibration.status` defaults to `incomplete`, `scenario_assessments` and `consistency_items` and `risk_dispositions` default to empty, `module_coverage.execution` defaults to `not_configured`, and 1.2 aliases `subject_kind`, `tasks_available`, `metadata.change`, and `artifacts.selected_change` remain in `tests/unit/test_report_contract.py`

### Implementation

- [X] T004 Add `Scenario.body`, `EvidenceScope`, `ScenarioAssessment`, `ConsistencyItem`, `CalibrationView`, `RiskDisposition`, `ModuleCoverage`, and schema `1.3` to `src/specguard/models/entities.py`, with `supported` requiring a positive `test_line`, `gap` and `unavailable` requiring `note`, and `conflict` requiring real line numbers on both sides
- [X] T005 Accept only `git.evidence_scope: range | target_tree` and default it to `range` in `src/specguard/config/models.py`
- [X] T006 Update existing `schema_version` expectations from `1.2` to `1.3` without changing behavioral assertions in `tests/integration/test_baseline_review.py`, `tests/integration/test_quickstart.py`, `tests/integration/test_us1_report.py`, and `tests/integration/test_speckit_review.py`

**Checkpoint**: 新字段可单独验证。未实现的故事仍不产生新的审核结论。

---

## Phase 3: User Story 1 - 按验收场景判断需求证据（Priority: P1）🎯 MVP

**Goal**: 每条需求只有一种主证据。验收场景单独标为已有测试支撑、覆盖缺口或不可用。

**Independent Test**: 准备含标识、仅文件名重叠、有效测试、恒真断言和无线索的样例。仅因文件名重叠或测试命令通过而被写成“已实现”的条目为 0。

### Tests for User Story 1

- [X] T007 [P] [US1] Add failing tests that direct evidence note is exactly `只代表找到关联，不代表验收场景已经通过`, inferred note is exactly `不能单独证明需求已经实现`, insufficient note is exactly `找不到实现证据`, a scenario is `supported` only when an in-scope test path contains the requirement identifier or scenario name, has one non-trivial assertion, and contains a whitespace-collapsed scenario body line of at least 8 characters, empty scenarios are `unavailable`, trivial assertions are `gap`, and assisted findings cannot set `supported` in `tests/unit/test_scenario_assessment.py`
- [X] T008 [P] [US1] Add a failing end-to-end test for those five evidence cases that leaves requirement artifacts and git history unchanged in `tests/integration/test_us1_evidence.py`

### Implementation for User Story 1

- [X] T009 [P] [US1] Store the text between a `#### Scenario:` heading and the next scenario or requirement in `Scenario.body` in `src/specguard/openspec/parser.py`
- [X] T010 [P] [US1] Store Spec Kit scenario body text in `Scenario.body` in `src/specguard/artifacts/speckit.py`
- [X] T011 [US1] Keep exactly one primary evidence item per requirement and use the three fixed notes in `src/specguard/review/traceability.py`
- [X] T012 [US1] Implement `supported | gap | unavailable` assessments without writing them back onto requirement evidence in `src/specguard/review/scenarios.py`
- [X] T013 [US1] Attach scenario assessments in `src/specguard/pipeline.py` and ignore assisted-review output when deciding `supported`
- [X] T014 [US1] Render scenario status, test path, and test line in `src/specguard/report/markdown.py` so they match the JSON from `src/specguard/report/json_report.py`

**Checkpoint**: 用户故事 1 可独立审核，主证据与场景结果分开。

---

## Phase 4: User Story 2 - 对照已接受的当前规范（Priority: P1）

**Goal**: 审核进行中的变更时指出未声明冲突，且不把当前规范需求并入变更清单。

**Independent Test**: 样例含一处未声明对立场景、一处已声明修改，以及一条只存在于当前规范的需求。报告只指出未声明冲突。

### Tests for User Story 2

- [X] T015 [P] [US2] Add failing tests that a conflict requires the same capability, the same title slug, opposite obligation words from `必须/应当/需要` versus `不得/禁止/不再`, and a shared phrase, that `modified` or `removed` declarations create no item, that unmatched wording is `human_review` rather than `conflict`, and that current-spec-only requirements stay out of the change requirement list in `tests/unit/test_consistency.py`
- [X] T016 [P] [US2] Add a failing end-to-end test for an undeclared conflict, a declared modification, a missing current spec saying `规范对照不可用`, and current-spec or Spec Kit review saying `未做 OpenSpec 当前规范对照` in `tests/integration/test_us2_consistency.py`

### Implementation for User Story 2

- [X] T017 [US2] Set `capability` from the parent directory of each change `spec.md` in `src/specguard/openspec/parser.py`
- [X] T018 [US2] Compare current specs as context only and emit `conflict` or `human_review` items in `src/specguard/review/consistency.py`
- [X] T019 [US2] Load that context only when the selected subject is an OpenSpec change in `src/specguard/pipeline.py`
- [X] T020 [US2] Show both source locations for conflicts in `src/specguard/report/markdown.py`

**Checkpoint**: 用户故事 2 可独立验证，已声明增量不被当成冲突。

---

## Phase 5: User Story 3 - 记录历史误报与漏报（Priority: P1）

**Goal**: 读取报告目录中的对照记录，拒绝虚假完成标记，并且不改变默认建议策略。

**Independent Test**: 缺失、不完整、虚假完成和一次完整历史审核四种记录中，前三种为未完成，第四种写出数量 1。四种默认都不阻止合并。

### Tests for User Story 3

- [X] T021 [P] [US3] Add failing tests that a review is complete only when every `finding_id` has exactly one `true_issue` or `false_positive` verdict, unknown ids do not count, and exactly one of `no_misses: true` or a non-empty `misses` list is set, that `complete: true` with zero complete reviews sets `rejected_complete_mark`, that a missing or unreadable file stays `incomplete`, and that `decide()` does not block because calibration is complete in `tests/unit/test_calibration.py`
- [X] T022 [P] [US3] Add a failing end-to-end test for the four ledger files, secret redaction, and advisory exit behavior in `tests/integration/test_us3_calibration.py`

### Implementation for User Story 3

- [X] T023 [US3] Read only `<report dir>/calibration.json` inside the resolved report directory and apply the completion rules in `src/specguard/review/calibration.py`
- [X] T024 [US3] Attach `CalibrationView` in `src/specguard/pipeline.py`, redact secrets with `src/specguard/llm/redact.py`, and leave blocking decisions in `src/specguard/review/policy.py`
- [X] T025 [US3] State `历史对照未完成` or the completed review count, including a rejected complete mark, in `src/specguard/report/markdown.py`

**Checkpoint**: 用户故事 3 可独立验证。对照完成不把默认结果改成阻断。

---

## Phase 6: User Story 4 - 补齐已承诺的代码风险（Priority: P2）

**Goal**: 九类风险每次都有处置。已证实只来自现有确定性模式，且不编造行号。

**Independent Test**: 空 catch、空的空值判断和集合长度上界给出已证实发现。没有这些线索的类别写明缺少上下文。写成“代码安全”的条目为 0。

### Tests for User Story 4

- [X] T026 [P] [US4] Add failing tests that all nine classes `boundary`, `exception`, `null_empty`, `transaction`, `concurrency`, `authorization`, `compatibility`, `persisted_data`, and `dependency_config` appear once, that `confirmed` is limited to an empty catch, an empty null check, and a `<= size/length` comparison with a real line and failure path, and that a file-level hint without a line uses `missing_context` instead of line 1 in `tests/unit/test_risk_classes.py`
- [X] T027 [P] [US4] Add a failing end-to-end test that an empty diff still lists all nine classes and keeps the disclaimer that no findings do not mean the code is safe in `tests/integration/test_us4_risk.py`

### Implementation for User Story 4

- [X] T028 [US4] Emit one `RiskDisposition` per class from the changed diff only in `src/specguard/review/risk.py`
- [X] T029 [US4] Copy those dispositions onto the report in `src/specguard/pipeline.py`
- [X] T030 [US4] List the nine classes and the no-safety disclaimer in `src/specguard/report/markdown.py`

**Checkpoint**: 用户故事 4 可独立验证，风险检查仍只看差异文件。

---

## Phase 7: User Story 5 - 明确当前规范的证据范围（Priority: P2）

**Goal**: 默认仍使用版本范围。只有当前规范可以显式改用目标版本的完整内容。

**Independent Test**: 同一份当前规范在默认范围下不引用范围外文件。`target-tree` 写明目标版本树。用于变更时退出 `4` 且不写报告。

### Tests for User Story 5

- [X] T031 [P] [US5] Add failing tests that `range` ignores files outside the diff, `target_tree` reads blobs at the resolved target and does not mark those files as diff changes, uncommitted files enter only with inclusion enabled, and a non-current subject fails before checks in `tests/unit/test_evidence_scope.py`
- [X] T032 [P] [US5] Add a failing end-to-end test that `--evidence-scope target-tree` on a change exits `4` with stderr containing `完整内容证据范围只适用于当前规范` and writes no report in `tests/integration/test_us5_evidence_scope.py`

### Implementation for User Story 5

- [X] T033 [US5] List the target tree and read file bytes from that revision in `src/specguard/git/diff.py`
- [X] T034 [US5] Accept `--evidence-scope range|target-tree` and reject `target-tree` unless the subject is an OpenSpec current spec before checks in `src/specguard/cli/main.py`
- [X] T035 [US5] Use the selected evidence files for traceability and scenario assessment only, while risk review continues to use the diff, in `src/specguard/pipeline.py`
- [X] T036 [US5] State whether the report used `range` or `target_tree` in `src/specguard/report/markdown.py`

**Checkpoint**: 用户故事 5 可独立验证。不传新选项时，版本范围行为与现在一致。

---

## Phase 8: User Story 6 - 说明构建和测试覆盖了哪些模块（Priority: P3）

**Goal**: 多模块变更说明仓库级命令没有按模块分别执行。未执行不得写成通过，也不得编造命令。

**Independent Test**: 变更触及两个模块且只配置了一次仓库级构建时，两个模块都被点名。无法识别布局时只说明限制。

### Tests for User Story 6

- [X] T037 [P] [US6] Add failing tests that changed files map to the nearest parent containing a build descriptor, two modules plus a repository-level build produce a `module-separation` check with status skipped and an empty command, one module does not appear as uncovered, and an unrecognized layout sets `execution` to `unrecognized` without a generated command in `tests/unit/test_module_coverage.py`
- [X] T038 [P] [US6] Add a failing end-to-end test naming both uncovered modules and leaving the repository-level build result unchanged in `tests/integration/test_us6_modules.py`

### Implementation for User Story 6

- [X] T039 [US6] Map changed paths to build modules in `src/specguard/project/detect.py`
- [X] T040 [US6] Add the skipped `module-separation` check only when execution is `repository` and more than one changed module exists in `src/specguard/pipeline.py`
- [X] T041 [US6] Name modules that were not checked separately in `src/specguard/report/markdown.py`

**Checkpoint**: 用户故事 6 可独立验证，且不把仓库级成功改写成每个模块都通过。

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: 把版本、说明和整套回归对齐 v0.4。

- [X] T042 [P] Set the product version to `0.4.0` in `pyproject.toml`, `src/specguard/__init__.py`, and `tests/unit/test_install_entry.py`
- [X] T043 [P] Document evidence scope, `calibration.json`, nine risk classes, and module coverage, and replace version `0.3.0` with `0.4.0`, in `README.md`, `README.en.md`, `docs/usage.md`, `docs/install.md`, `docs/operations.md`, and `docs/config-templates.md`
- [X] T044 [P] Add a failing-then-passing budget test that 1000 requirements and 2000 evidence files finish linkage within 5 seconds excluding build, test, and model calls in `tests/unit/test_evidence_budget.py`
- [X] T045 Run `.venv/bin/python -m pytest -q` from the repository root and record the command result in `specs/005-close-review-gaps/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup（Phase 1）**: 无前置，可立即开始
- **Foundational（Phase 2）**: 依赖 Setup，并阻塞全部用户故事
- **User Stories（Phase 3+）**: 都依赖 Foundational 完成
  - 之后可按人员并行
  - 或按 P1 → P2 → P3 顺序
- **Polish（Phase 9）**: 依赖想交付的用户故事全部完成

### User Story Dependencies

- **User Story 1（P1）**: Foundational 之后即可开始，不依赖其他故事
- **User Story 2（P1）**: Foundational 之后即可开始。它读取当前规范作为对照，不依赖故事 1 的场景结论
- **User Story 3（P1）**: Foundational 之后即可开始，不依赖故事 1 或 2
- **User Story 4（P2）**: Foundational 之后即可开始。风险只看差异，不依赖新的证据范围
- **User Story 5（P2）**: Foundational 之后即可开始。它改变追溯和场景评估的可读文件；若与故事 1 并行，只在 `pipeline.py` 汇合
- **User Story 6（P3）**: Foundational 之后即可开始，不依赖前面的证据规则

### Within Each User Story

- 先写该故事的测试并确认失败
- 解析和模型先于审核函数
- 审核函数先于 `pipeline.py`
- 报告呈现放在该故事最后
- 共享文件 `pipeline.py`、`markdown.py` 和 `openspec/parser.py` 不要标成并行

### Parallel Opportunities

- T001 与 T002 可并行
- T003 通过并确认失败后，T004 与 T005 修改不同文件，可先后紧接完成
- 每个故事中标了 [P] 的测试可并行
- T009 与 T010 可并行
- Foundational 完成后，故事 1、2、3 可由不同人并行；汇合点只限共享的流水线和 Markdown 文件
- T042、T043、T044 可并行

---

## Parallel Example: User Story 1

```bash
# 先同时写两个失败测试：
Task: "Add failing evidence and scenario tests in tests/unit/test_scenario_assessment.py"
Task: "Add failing end-to-end evidence test in tests/integration/test_us1_evidence.py"

# 测试失败后，同时保存两种工件的场景正文：
Task: "Store OpenSpec scenario body in src/specguard/openspec/parser.py"
Task: "Store Spec Kit scenario body in src/specguard/artifacts/speckit.py"
```

---

## Implementation Strategy

### MVP First（只做用户故事 1）

1. 完成 Phase 1 和 Phase 2
2. 完成 Phase 3 的用户故事 1
3. **停下验证**：主证据三种状态和场景缺口符合独立测试
4. 演示需求证据已经能分开场景结果

### Incremental Delivery

1. Setup + Foundational → 旧审核结论保持不变
2. 用户故事 1 → 需求证据和场景覆盖
3. 用户故事 2 → 未声明冲突
4. 用户故事 3 → 历史对照记录
5. 用户故事 4 → 九类风险处置
6. 用户故事 5 → 显式证据范围
7. 用户故事 6 → 模块覆盖说明
8. Polish → 版本 v0.4 和完整 pytest

### Parallel Team Strategy

1. 一起完成 Setup 和 Foundational
2. Foundational 之后：
   - 开发者 A：用户故事 1
   - 开发者 B：用户故事 2
   - 开发者 C：用户故事 3
3. 随后再分用户故事 4、5、6。修改 `pipeline.py` 或 `markdown.py` 时一次只由一人集成

---

## Notes

- 不使用新选项时，OpenSpec 变更、当前规范和 Spec Kit 的现有选择与只读行为必须保持通过
- 对照完成不得修改 `policy.mode`，也不得因此把 `blocked` 设为真
- `target_tree` 误用必须在构建、测试和辅助审查之前失败
- 没有真实行号时，不得用第 1 行填充风险位置
- 每个故事完成后都可以单独停下来验证

## Phase 10: Convergence

- [X] T046 Name each calibration verdict whose finding id is outside that review's finding_ids in `CalibrationView.notes`, and keep the ledger incomplete, per FR-019 (partial)
- [X] T047 State the weakest requirement evidence, the undeclared conflict count, the calibration status, and the highest risk in that order in the Markdown summary per SC-007 (partial)
