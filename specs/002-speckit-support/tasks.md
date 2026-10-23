---
description: "Task list for SpecGuard Spec Kit requirements source"
---

# Tasks: SpecGuard 支持 Spec Kit 需求来源

**Input**: Design documents from `/specs/002-speckit-support/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 宪章要求 SpecGuard 自身的功能必须先有失败测试，再写实现。本清单包含测试任务。每个故事的测试必须先写并确认失败，然后才实现对应行为。

**Organization**: 宪章 1.1.0 已允许 Spec Kit 功能目录作为需求来源。任务按用户故事分组。先完成来源选择，再完成单个功能的报告，然后补任务证据、拒绝自动挑选和非 Java 限制。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件，且不依赖尚未完成的任务）
- **[Story]**: 任务所属用户故事（US1–US4）
- 设置阶段和基础阶段不标故事标签
- 描述中含精确文件路径

## Path Conventions

- 单一 Python 包：`src/specguard/`、`tests/` 位于仓库根目录
- 路径以 plan.md 的源码布局为准
- 现有 OpenSpec 夹具仍用 `tests/fixtures/materialize.py` 的 `materialize()`

## Phase 1: Setup

**Purpose**: 建立 Spec Kit 解析包，不改变现有审核行为

**Independent Test**: `src/specguard/speckit/` 可被导入，现有 `pytest` 仍通过。

- [ ] T001 创建 `src/specguard/speckit/__init__.py`，不在该文件中实现发现或解析

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 配置模型和功能目录发现。完成前不得把 Spec Kit 接入 `src/specguard/pipeline.py`

**Independent Test**: 配置接受 `requirements.source` 的 `auto`、`openspec`、`speckit`；多个功能目录在未指定名称时失败并列出目录名。

- [ ] T002 在 `tests/unit/test_requirements_source.py` 中编写失败测试：`src/specguard/config/models.py` 的 `SpecGuardConfig` 接受 `requirements.source` 为 `openspec`、`speckit` 或 `auto`，默认 `auto`；`speckit.root` 默认 `specs`；`speckit.feature` 可空，非空时必须与功能目录名完全一致；其他取值使配置无效
- [ ] T003 在 `src/specguard/config/models.py` 中增加上述字段，并保持未列出的字段仍被拒绝
- [ ] T004 [P] 在 `tests/unit/test_speckit_discover.py` 中编写失败测试：`specs/` 下只有「编号-名称」且含 `spec.md` 的目录是候选；没有 `spec.md` 或目录名不以编号开头的目录不是候选；零个候选时没有选中项；一个候选时选中它；多个候选且未提供 `speckit.feature` 时抛出用法错误并列出全部目录名，即使 `.specify/feature.json` 指向其中一个也不得选中，错误文本可以包含该文件中的路径
- [ ] T005 在 `src/specguard/speckit/discover.py` 中实现 T004 的发现和选择。`speckit.feature` 必须与目录名完全一致，否则失败并指出该名称

**Checkpoint**: 来源字段和目录选择可单测。审核流程仍只走 OpenSpec。

---

## Phase 3: User Story 1 - 审核一个 Spec Kit 功能 (Priority: P1)

**Goal**: 只有一个 Spec Kit 功能的 Java 仓库能得到含功能名、规格工件和五个问题章节的只读报告。

**Independent Test**: 用 `tests/fixtures/materialize.py` 物化单个功能夹具并调用 `src/specguard/pipeline.py` 的 `run_review`。报告包含功能名，规格和源文件字节与审核前一致。

### Tests

- [ ] T006 [P] [US1] 在 `tests/unit/test_speckit_parser.py` 中编写失败测试：`src/specguard/speckit/parser.py` 从 `spec.md` 识别 `FR-` 加数字的功能需求、用户故事和 Given、When、Then 验收场景；没有可核验需求时需求符合性不可用，不编造需求标识
- [ ] T007 [P] [US1] 在 `tests/integration/test_speckit_single.py` 中编写失败测试：夹具含 `pom.xml`、一个 `specs/001-sample/spec.md` 和 `specguard.yaml`；`run_review` 选中 `001-sample`；Markdown 含「需要人工审核」「需求覆盖」「潜在风险」「证据定位」和限制说明；`git status` 除报告目录外无变化，且不执行 Spec Kit 命令

### Implementation

- [ ] T008 [US1] 在 `src/specguard/speckit/parser.py` 中把规格条目映射到现有需求实体。功能需求标识是 `FR-` 加数字。用户故事标题和验收场景进入报告，但标题相似不得成为直接证据
- [ ] T009 [US1] 在 `src/specguard/cli/main.py` 增加 `--feature`，并在 `src/specguard/pipeline.py` 的构建和测试之前，对单个 Spec Kit 功能调用解析结果。`--feature` 覆盖 `speckit.feature`。报告写明功能名和缺失工件

**Checkpoint**: 单个 Spec Kit 功能可以独立演示。

---

## Phase 4: User Story 2 - 已勾选任务必须有支撑 (Priority: P1)

**Goal**: `tasks.md` 的勾选状态进入现有任务模型。已完成但没有代码或测试支撑的任务成为完整性缺口。

**Independent Test**: 一条 `FR-001` 出现在变更文件内容中则为直接证据；只有文件名重叠则不是直接证据；一条 `- [x]` 任务没有支撑时出现「已标为完成，但缺少代码或测试支撑」。

### Tests

- [ ] T010 [P] [US2] 在 `tests/unit/test_speckit_task_evidence.py` 中编写失败测试：只认 `- [ ]`、`- [x]`、`- [X]`；缺少 `tasks.md` 时记录任务工件缺失且不合成已完成任务；变更文件内容包含 `FR-001` 才是直接证据；仅文件名重叠不是直接证据；`marked_complete` 为真且没有代码或测试支撑时，`support` 为 `none` 并计入任务完整性缺口，摘要不得写成代码一定有错

### Implementation

- [ ] T011 [US2] 在 `src/specguard/speckit/parser.py` 中解析 `tasks.md` 并映射到现有任务实体。已勾选行是 `- [x]` 或 `- [X]`
- [ ] T012 [US2] 在 `src/specguard/pipeline.py` 中把 Spec Kit 任务交给现有 `src/specguard/review/traceability.py` 的 `link_requirements` 和 `link_tasks`，不新增证据等级

**Checkpoint**: 需求证据和任务缺口可独立验证。

---

## Phase 5: User Story 3 - 不悄悄改掉 OpenSpec，也不自动挑一个功能 (Priority: P1)

**Goal**: OpenSpec 行为不变。多个功能或两种来源未指定时，在检查前退出 `4`，不写报告。

**Independent Test**: 两个 Spec Kit 功能不传 `--feature` 时退出 `4` 且报告文件数为 0。现有 `single_change` 夹具仍按 `--change` 审核。

### Tests

- [ ] T013 [P] [US3] 在 `tests/integration/test_speckit_selection.py` 中编写失败测试：多个功能且未指定时退出 `4` 并列出全部目录名，不创建报告文件；`requirements.source` 为 `auto` 且两种来源都有候选时退出 `4` 并同时提到 `openspec` 和 `speckit`；来源为 `speckit` 时再传 `--change` 退出 `4`；来源为 `openspec` 时再传 `--feature` 退出 `4`；`--feature` 名称不存在时退出 `4` 并指出该名称
- [ ] T014 [P] [US3] 在 `tests/integration/test_openspec_regression.py` 中编写失败测试：`tests/fixtures/single_change` 不传 `--feature` 时，所选变更、证据级别和只读结果与增加 Spec Kit 支持之前一致

### Implementation

- [ ] T015 [US3] 在 `src/specguard/pipeline.py` 中实现来源选择。`auto` 只在恰好一种来源有候选时解析成该来源。停止发生在构建、测试和模型请求之前，并且不创建报告文件

**Checkpoint**: OpenSpec 回归和拒绝自动挑选可独立验证。

---

## Phase 6: User Story 4 - 超出范围时说明不支持 (Priority: P2)

**Goal**: 非 Java 的 Spec Kit 仓库不得得到代码风险或测试已经通过的结论。

**Independent Test**: 没有 `pom.xml` 和 Gradle 构建文件的 Spec Kit 夹具，限制说明包含「无法可靠识别 Java 项目布局。未猜测构建命令。」需求符合性不得标成通过。

### Tests

- [ ] T016 [P] [US4] 在 `tests/integration/test_speckit_not_java.py` 中编写失败测试：夹具有唯一 Spec Kit 功能但没有 Java 构建文件；报告限制说明包含 `src/specguard/project/detect.py` 的「无法可靠识别 Java 项目布局。未猜测构建命令。」；不发明构建命令；需求符合性、代码风险和测试不得写成已经通过

### Implementation

- [ ] T017 [US4] 在 `src/specguard/pipeline.py` 中对非 Java 布局保留 `detect_project` 的限制说明，不把需求符合性标成通过，也不运行猜测出的 Maven 或 Gradle 命令

**Checkpoint**: 非 Java 限制可独立验证。

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 使用说明和配置模板告诉工程师如何指定 Spec Kit 功能

**Independent Test**: `docs/usage.md` 含 `--feature`。三档模板仍是 `review.mode: static` 和 `review.policy: advisory`。

- [ ] T018 [P] 在 `docs/usage.md` 写明单个 Spec Kit 功能可直接审核，多个功能使用 `--feature`，两种来源同时存在时必须指定 `requirements.source`
- [ ] T019 [P] 在 `docs/config-templates.md` 的三档 YAML 中说明 `requirements.source` 默认 `auto`、`speckit.feature` 可空。不得把 `review.policy` 改成 `strict`，不得写入 `llm.base_url`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 无前置，完成后才能开始 Phase 2
- Phase 2 挡住全部用户故事。T003 依赖 T002，T005 依赖 T004
- Phase 3 依赖 Phase 2。T008 依赖 T006，T009 依赖 T007 和 T008
- Phase 4 依赖 Phase 3 的解析器和流程。T011 依赖 T010，T012 依赖 T011
- Phase 5 的测试可在 Phase 2 之后编写；T015 依赖 T009，并依赖 T013 与 T014 已失败
- Phase 6 依赖 T009。T017 依赖 T016，并在 T015 之后修改 `src/specguard/pipeline.py`
- Phase 7 依赖 Phase 3 至 Phase 6 的行为已经存在

### User Story Order

- US1 是第一条可演示的审核路径
- US2 使用 US1 的解析结果，补上任务证据
- US3 保护 OpenSpec，并拒绝自动挑选
- US4 依赖已经接入的流程来写明非 Java 限制

### Parallel Opportunities

- T004 可与 T002 并行
- T006 与 T007 可并行
- T010 可与 T006、T007 并行编写，但 T011 必须在 T008 之后
- T013 与 T014 可并行
- T016 可与 T013、T014 并行编写
- T018 与 T019 可并行
- `src/specguard/pipeline.py` 上的 T009、T012、T015、T017 必须按此顺序执行

---

## Parallel Example: User Story 3

```text
Task: "T013 tests/integration/test_speckit_selection.py"
Task: "T014 tests/integration/test_openspec_regression.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. 完成 Phase 1 和 Phase 2
2. 完成 Phase 3，确认单个 Spec Kit 功能能出只读报告
3. 停下来验证报告章节和仓库未被修改

### Incremental Delivery

1. US2 补上任务勾选和证据级别
2. US3 锁住 OpenSpec 回归和退出码 `4`
3. US4 锁住非 Java 的诚实限制
4. Phase 7 更新使用说明和配置模板

### Parallel Team Strategy

1. 一人先完成 T001 至 T005
2. 之后可同时编写 T006、T007、T010、T013、T014、T016
3. 实现仍按解析器、命令行、然后多次修改 `src/specguard/pipeline.py` 的顺序进行
