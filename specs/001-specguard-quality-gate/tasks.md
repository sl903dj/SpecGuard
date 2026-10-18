---
description: "Task list for SpecGuard v0.1 change-quality review"
---

# Tasks: SpecGuard 变更质量守卫

**Input**: Design documents from `/specs/001-specguard-quality-gate/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 宪章要求 SpecGuard 自身的功能必须先有失败测试，再写实现。本清单包含测试任务。每个故事的测试必须先写并确认失败，然后才实现对应行为。

**Organization**: 任务按用户故事分组。推荐完成顺序遵循 plan.md 的交付顺序：基础 → US1 报告 → US2 需求解析与追溯 → US3 确定性检查 → US4/US5 → US6 辅助审查 → US7 严格策略。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件，且不依赖尚未完成的任务）
- **[Story]**: 任务所属用户故事（US1–US7）
- 设置阶段和基础阶段不标故事标签
- 描述中含精确文件路径

## Path Conventions

- 单一 Python 包：`src/specguard/`、`tests/` 位于仓库根目录
- 路径以 plan.md 的源码布局为准

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 建立可测试的 Python 包，不包含审核行为

- [X] T001 按 plan.md 创建包目录 `src/specguard/{cli,config,models,git,openspec,project,checks,review,llm,report}` 和 `tests/{unit,integration,fixtures}`，并添加各目录的 `__init__.py`
- [X] T002 在 `pyproject.toml` 中声明 Python `>=3.11`、Typer、Pydantic v2、pytest、httpx，配置 `pytest` 的 `testpaths = ["tests"]`，并写明依赖版本在实现时按内网环境锁定
- [X] T003 [P] 在 `.gitignore` 中忽略 `.venv/`、`__pycache__/`、`.pytest_cache/` 和 `.specguard/reports/`
- [X] T004 [P] 在 `tests/conftest.py` 中添加夹具根路径 `tests/fixtures`，供后续故事复用

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有故事共用的配置、状态模型和命令骨架。完成前不得开始用户故事

**⚠️ CRITICAL**: 用户故事必须等本阶段完成

### Tests（先写，先失败）

- [X] T005 [P] 在 `tests/unit/test_config.py` 中编写失败测试：`version` 只接受 `1`；`review.llm_findings_block` 只接受 `false`；`llm.external_fallback` 只接受 `false`；未知字段、允许列表外命令、空的 `assisted` 模型地址使加载失败且不开始审核
- [X] T006 [P] 在 `tests/unit/test_report_paths.py` 中编写失败测试：`report.output_dir` 解析后必须仍在允许的报告根内；包含 `..` 逃逸、指向源文件或 Git 元数据的路径校验失败
- [X] T007 [P] 在 `tests/unit/test_status_models.py` 中编写失败测试：检查状态只能是 `PASS`、`FAIL`、`SKIPPED`、`ERROR`、`TIMEOUT` 之一，且 `SKIPPED`、`ERROR`、`TIMEOUT` 不能被写成 `PASS`；整次状态只能是 `REVIEW_COMPLETE`、`REVIEW_INCOMPLETE`、`POLICY_BLOCKED`

### Implementation

- [X] T008 在 `src/specguard/config/models.py` 中定义配置模型，拒绝未知字段。`review.policy` 只允许 `advisory` 或 `strict`，默认 `advisory`。`review.mode` 只允许 `static` 或 `assisted`，默认 `static`。`review.llm_findings_block` 在 v0.1 只接受 `false`
- [X] T009 在 `src/specguard/config/loader.py` 中加载 `specguard.yaml`，校验失败时返回用法错误且不执行检查，错误信息包含字段路径
- [X] T010 在 `src/specguard/config/allowlist.py` 中维护允许的构建、测试和已命名工具命令；列表外命令视为配置无效
- [X] T011 在 `src/specguard/report/paths.py` 中实现报告路径校验，拒绝逃逸出报告根、覆盖源文件或写入 Git 元数据的目标
- [X] T012 在 `src/specguard/models/status.py` 与 `src/specguard/models/entities.py` 中实现 `CheckResult`、`Evidence`、`Finding`、`ReviewPolicy`、`ReviewReport`。`Evidence.status` 只允许 `direct`、`inferred`、`insufficient`。`Finding.evidence_status` 只允许 `confirmed`、`hypothesis`、`insufficient`。`Finding.severity` 只允许 `critical`、`high`、`medium`、`low`、`info`
- [X] T013 在 `src/specguard/cli/exit_codes.py` 中定义退出码：`0` OK、`1` INTERNAL、`2` POLICY_BLOCKED、`3` INCOMPLETE、`4` USAGE
- [X] T014 在 `src/specguard/cli/main.py` 中实现 `version`、`--help` 和 `config validate`。前两者退出 `0` 且不运行审核；`config validate` 只校验配置

**Checkpoint**: 配置、状态和命令骨架可测。用户故事可以开始

---

## Phase 3: User Story 1 - 获得一份可核查的变更质量报告 (Priority: P1) 🎯 MVP

**Goal**: 对一个有效版本库运行审核，写出带免责声明的 Markdown 和 JSON 报告，并且不改动被审核仓库

**Independent Test**: 对准备好的变更运行一次审核。报告包含人工审核提示、需求覆盖、潜在风险、证据定位和限制说明；除报告目录外，源文件、需求工件和版本历史不变

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] 在 `tests/unit/test_git_readonly.py` 中编写失败测试：非版本库在检查前停止并给出可操作错误；无法解析的基线必须报错且不得替换成其他版本；实现不得调用 `add`、`commit`、`checkout`、`reset`、`merge` 或 `clean`
- [X] T016 [P] [US1] 在 `tests/unit/test_report_contract.py` 中编写失败测试：JSON `schema_version` 为 `"1.0"`；必填键缺失时使用 `null` 或空数组而不是省略；没有发现时仍列出实际执行的检查，并声明这不是“代码没有缺陷”；固定限制说明必须出现
- [X] T017 [P] [US1] 在 `tests/integration/test_us1_report.py` 中编写失败测试：一次审核同时写出 Markdown 和 JSON，章节包含需要人工审核、需求覆盖、潜在风险、证据定位；`metadata` 记录实际基线与目标；工作区除报告目录外干净

### Implementation for User Story 1

- [X] T018 [US1] 在 `src/specguard/git/repository.py` 中实现版本库根识别、基线与目标解析，以及开始和结束时的 `head_sha` 指纹。`resolved_base` 与 `resolved_target` 必须写入报告，不得悄悄替换
- [X] T019 [US1] 在 `src/specguard/git/diff.py` 中实现变更文件列表。`change_type` 只允许 `added`、`modified`、`deleted`、`renamed`，并且必须来自 Git；`committed` 把已提交变更和未提交变更分开；默认不纳入工作区
- [X] T020 [P] [US1] 在 `src/specguard/report/markdown.py` 中按 `contracts/report.md` 写出必含章节和限制说明。不完整审核不得使用表示干净通过的标题
- [X] T021 [P] [US1] 在 `src/specguard/report/json_report.py` 中从同一 `ReviewReport` 写出 `schema_version` 为 `"1.0"` 的 JSON，不省略必填键
- [X] T022 [US1] 在 `src/specguard/pipeline.py` 和 `src/specguard/cli/review_command.py` 中把只读差异接到报告写出。尚无需求或检查时，对应章节标为不可用或未执行，不得宣称需求符合性通过
- [X] T023 [US1] 在 `src/specguard/pipeline.py` 中比较审核前后的 `head_sha`。指纹不一致时整次状态为 `REVIEW_INCOMPLETE`，退出码为 `3`

**Checkpoint**: User Story 1 可独立演示。报告诚实，仓库保持只读

---

## Phase 4: User Story 2 - 核对需求符合性与任务完整性 (Priority: P1)

**Goal**: 读取所选 OpenSpec 变更，把需求与任务标成直接证据、推断或证据不足，且不把证据不足写成代码缺陷

**Independent Test**: 用含有已实现需求、无证据需求、含糊需求、被修改或删除的需求，以及已勾选但无支撑任务的夹具运行审核。报告按情况标注，不把缺口写成确定缺陷

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] 在 `tests/unit/test_openspec_parser.py` 中编写失败测试：解析 `ADDED`、`MODIFIED`、`REMOVED` 和任务勾选，并保留源文件与行号；多个进行中变更且未选择时失败；找不到 OpenSpec 时需求审核不可用
- [X] T025 [P] [US2] 在 `tests/unit/test_traceability.py` 中编写失败测试：`Evidence.status` 只允许 `direct`、`inferred`、`insufficient`；仅有文件重叠只能产生 `inferred`；已勾选且 `support` 为 `none` 的任务形成完整性缺口，不得标成实现错误；无法追溯的行为标成可能的擅自扩展并要求人工审核
- [X] T026 [P] [US2] 在 `tests/integration/test_us2_requirements.py` 中编写失败测试：删除的需求不自动成为缺陷；含糊需求带有 `ambiguity_reason`；工件缺失列表出现在报告的 `artifacts` 中

### Implementation for User Story 2

- [X] T027 [US2] 在 `src/specguard/openspec/discover.py` 中定位 `openspec/`，枚举进行中变更。`openspec.require_change_selection` 为真且未选择时退出 `4`，不得自动挑选
- [X] T028 [US2] 在 `src/specguard/openspec/parser.py` 中解析 proposal、design、tasks 和增量规范。需求的 `change_semantics` 只允许 `added`、`modified`、`removed`。任务没有勾选标记时 `marked_complete` 为否，不猜测完成状态
- [X] T029 [US2] 在 `src/specguard/review/traceability.py` 中关联需求、任务和变更文件。`TaskItem.support` 只允许 `code`、`test`、`both`、`none`。没有关联时使用 `insufficient`
- [X] T030 [US2] 在 `src/specguard/report/markdown.py` 和 `src/specguard/report/json_report.py` 中写入需求覆盖计数、任务缺口和证据定位，并保持两种报告一致

**Checkpoint**: User Story 1 和 User Story 2 都能独立验证。没有检查结果时，测试证据保持 `insufficient`

---

## Phase 5: User Story 3 - 在没有辅助审查时完成基础质量检查 (Priority: P1)

**Goal**: 静态模式执行已配置的确定性检查，五种状态互不混用，辅助维度标为未执行

**Independent Test**: 不配置模型。构建成功、构建失败、工具缺失和超时得到 `PASS`、`FAIL`、`SKIPPED` 或 `ERROR`、`TIMEOUT`。必需检查未完成时退出 `3`，报告为 `REVIEW_INCOMPLETE`

### Tests for User Story 3 ⚠️

- [X] T031 [P] [US3] 在 `tests/unit/test_check_runner.py` 中编写失败测试：成功记录命令、耗时和退出码；失败保留不超过 `security.max_command_output_bytes` 的诊断；超时标为 `TIMEOUT` 并终止进程组；非必需工具缺失为 `SKIPPED`，必需工具缺失为 `ERROR`，两者都不是 `PASS`
- [X] T032 [P] [US3] 在 `tests/unit/test_java_project.py` 中编写失败测试：识别 Maven 与 Gradle 及 wrapper 和多模块；无法识别时说明限制；未配置命令时不猜测 `mvn test` 或 `gradle test`
- [X] T033 [P] [US3] 在 `tests/integration/test_us3_static_checks.py` 中编写失败测试：`--mode static` 不发起模型请求，辅助维度为 `SKIPPED`；必需检查失败或超时时退出码为 `3`

### Implementation for User Story 3

- [X] T034 [US3] 在 `src/specguard/checks/runner.py` 中执行允许列表内的子进程，强制超时、输出上限和进程组终止。状态一旦写出，不得改成另一种成功
- [X] T035 [US3] 在 `src/specguard/project/detect.py` 中识别 `pom.xml`、`build.gradle`、`build.gradle.kts` 和 wrapper，并列出模块。不得静默漏掉受影响模块
- [X] T036 [US3] 在 `src/specguard/checks/java.py` 中只执行配置里且位于允许列表中的构建与测试命令。启用但没有命令的必需检查为 `ERROR`，非必需为 `SKIPPED`
- [X] T037 [US3] 在 `src/specguard/checks/optional_tools.py` 中接入 Checkstyle、SpotBugs、PMD、JaCoCo、ArchUnit 和 `openspec validate`。工具不存在时按 `required` 标为 `ERROR` 或 `SKIPPED`
- [X] T038 [US3] 在 `src/specguard/pipeline.py` 中于静态模式下运行检查并把 `CheckResult` 写入报告。未配置辅助审查时四个辅助维度保持 `SKIPPED`。必需检查落入 `SKIPPED`、`ERROR` 或 `TIMEOUT` 时，整次状态为 `REVIEW_INCOMPLETE`

**Checkpoint**: 静态模式可以独立运行。到此为止，计划中的“先有确定性检查再谈模型”已经成立

---

## Phase 6: User Story 4 - 标出代码风险并安排审核顺序 (Priority: P2)

**Goal**: 报告指出边界、异常、兼容性和回归风险，最高风险在前，冲突不被收成一个干净结论

**Independent Test**: 用含有边界问题、异常处理问题和公开接口变化的样例审核。每条疑点有位置和说得通的失败路径；可靠检查与待复核假设分开

### Tests for User Story 4 ⚠️

- [X] T039 [P] [US4] 在 `tests/unit/test_risk_review.py` 中编写失败测试：业务逻辑疑点没有 `failure_path` 时不得写成缺陷；位置未知时 `location` 为 `null`，不得填 `0` 或假行号；既有测试失败不得在无证据时归因于当前变更
- [X] T040 [P] [US4] 在 `tests/unit/test_finding_normalization.py` 中编写失败测试：重复发现可以归组，但必须保留各自 `origin`；互相冲突的结论进入 `conflicts`，不得合成折中结果。`summary.reliable_checks` 只收录 `PASS` 或已确认 `FAIL`，不收录 `SKIPPED`、`ERROR`、`TIMEOUT`

### Implementation for User Story 4

- [X] T041 [US4] 在 `src/specguard/review/risk.py` 中根据变更文件和可用上下文产生业务逻辑与回归发现。`Finding.category` 使用 `business_logic` 或 `regression`。模型尚未接入时，这些规则型发现的 `evidence_status` 为 `confirmed` 或 `insufficient`，不得假装来自模型
- [X] T042 [US4] 在 `src/specguard/review/ranking.py` 中按 `critical`、`high`、`medium`、`low`、`info` 排列 `summary.highest_risks`，并填写 `summary.reliable_checks`
- [X] T043 [US4] 在 `src/specguard/report/markdown.py` 与 `src/specguard/report/json_report.py` 中使用同一排序写出潜在风险。已有可靠证据的检查标为不必反复人工确认

**Checkpoint**: 工程师可以只看报告摘要决定先审核哪里

---

## Phase 7: User Story 5 - 判断测试是否真正验证了需求 (Priority: P2)

**Goal**: 区分测试通过、测试失败和测试未能执行，并标出没有验证需求的简单断言与缺失的边界测试

**Independent Test**: 三类样例分别得到“通过但不等于需求满足”“FAIL”和“执行错误”。没有覆盖率数据时不出现编造的百分比

### Tests for User Story 5 ⚠️

- [X] T044 [P] [US5] 在 `tests/unit/test_test_adequacy.py` 中编写失败测试：测试命令成功不得把需求改成已满足；测试失败与测试未能执行必须分开；重要边界、反向场景或异常场景缺少证据时产生 `test_adequacy` 关注点；覆盖率不可用时不得写入百分比

### Implementation for User Story 5

- [X] T045 [US5] 在 `src/specguard/checks/test_results.py` 中读取已配置测试命令产出的结果文件。文件不存在时标为不可用，不编造通过数或覆盖率
- [X] T046 [US5] 在 `src/specguard/review/test_adequacy.py` 中把测试结果关联到需求和变更路径。只含不能验证该需求的简单断言时，证据状态保持 `insufficient`，并生成测试有效性发现
- [X] T047 [US5] 在 `src/specguard/pipeline.py` 中把测试有效性发现写入报告，且不覆盖 User Story 2 已经标成证据不足的需求结论

**Checkpoint**: 测试通过不再被报告表述成所有需求已满足

---

## Phase 8: User Story 6 - 在内网使用辅助审查且不外泄材料 (Priority: P2)

**Goal**: 只有显式配置的内部模型会被调用；其输出默认是假设；密钥不进入提示或报告

**Independent Test**: 未配置、服务拒绝连接、返回无法解析、源码夹带审核指示这四种情况都不改送其他服务，已成功的确定性检查仍保留

### Tests for User Story 6 ⚠️

- [X] T048 [P] [US6] 在 `tests/unit/test_llm_client.py` 中编写失败测试：未配置时零网络请求且辅助维度为 `SKIPPED`；只允许配置的 `base_url` 主机；不可达或无法解析时该维度为 `ERROR`；`llm.external_fallback` 不能打开第二条线路
- [X] T049 [P] [US6] 在 `tests/unit/test_secret_redaction.py` 中编写失败测试：疑似密钥在送审前被遮盖；报告只记录已遮盖的次数和位置类别，不记录原文；源码中的审核指示不能把策略改成通过

### Implementation for User Story 6

- [X] T050 [US6] 在 `src/specguard/llm/redact.py` 中遮盖常见密钥和令牌。`report.include_source_snippets` 默认 `false`；只有显式开启才允许短片段，且片段也要先遮盖
- [X] T051 [US6] 在 `src/specguard/llm/client.py` 中实现带超时和有限重试的内网 OpenAI 兼容客户端。`api_key_env` 只读取环境变量名，密钥不写入配置、日志或报告
- [X] T052 [US6] 在 `src/specguard/review/assisted.py` 中构造不超过 `llm.max_context_chars` 的变更上下文。没有确定性证据支持的模型发现，`evidence_status` 必须是 `hypothesis`
- [X] T053 [US6] 在 `src/specguard/pipeline.py` 中仅当 `--mode assisted` 且配置完整时调用模型。模型失败不得丢弃已完成的 `CheckResult`

**Checkpoint**: 静态模式仍然不需要模型。辅助审查失败时报告保持不完整或错误，而不是干净通过

---

## Phase 9: User Story 7 - 按策略给出建议或阻断信号 (Priority: P3)

**Goal**: 默认建议模式只把发现写入报告。严格模式只让已确认的确定性失败产生阻断信号

**Independent Test**: 同一组确定性失败在 `advisory` 下退出 `0` 且 `policy.blocked` 为假；在 `strict` 且必需检查都完成时退出 `2`。纯模型假设不导致退出 `2`

### Tests for User Story 7 ⚠️

- [X] T054 [P] [US7] 在 `tests/unit/test_policy.py` 中编写失败测试：`advisory` 下 `blocked` 恒为否；`strict` 下只有 `evidence_status` 为 `confirmed` 且严重程度位于 `block_on` 的确定性失败才使 `blocked` 为真；模型假设不阻断；必需检查未完成时退出码取 `3` 而不是 `2`

### Implementation for User Story 7

- [X] T055 [US7] 在 `src/specguard/review/policy.py` 中实现 `ReviewPolicy`。`llm_findings_block` 保持为否。默认配置不得把策略改成阻断式合并门禁
- [X] T056 [US7] 在 `src/specguard/cli/review_command.py` 中按 `contracts/cli.md` 映射退出码：完成且未阻断为 `0`，严格阻断为 `2`，不完整为 `3`，用法错误为 `4`，未预期错误为 `1`

**Checkpoint**: 全部故事都可独立验证。默认路径仍是建议模式

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: 夹具、隔离构建和 quickstart 抽查

- [X] T057 [P] 在 `tests/fixtures/` 中添加小型 Git 夹具：单变更 Java 样例、两个进行中变更、非法配置、无证据需求和已勾选但无支撑的任务
- [X] T058 [P] 在 `src/specguard/checks/isolate.py` 中实现 `security.isolate_builds: true` 时于临时副本执行构建。隔离失败时对应检查为 `ERROR`，不是 `PASS`
- [X] T059 [P] 在 `tests/integration/test_readonly_repository.py` 中断言审核前后业务源文件、OpenSpec 工件、Git 索引和提交历史一致
- [X] T060 [P] 在 `docs/report-interpretation.md` 中说明五种检查状态、三种整次状态，以及“证据不足不是缺陷、检查未发现问题不是安全”
- [X] T061 按 `specs/001-specguard-quality-gate/quickstart.md` 在 `tests/integration/test_quickstart.py` 中自动化场景 1 至 8，并记录场景 9 的人工抽查项

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无前置，可立即开始
- **Foundational (Phase 2)**: 依赖 Phase 1，阻塞全部用户故事
- **User Stories (Phase 3–9)**: 都依赖 Phase 2
- **Polish (Phase 10)**: 依赖希望交付的那些故事。静态模式抽查至少需要 US1、US2、US3

### User Story Dependencies

- **US1 (P1)**: 只依赖基础阶段。这是 MVP
- **US2 (P1)**: 依赖 US1 的报告写出，以便把覆盖结果放进同一份报告。解析测试可在报告集成之前单独运行
- **US3 (P1)**: 依赖 US1 的流水线。计划要求 OpenSpec 解析先于检查，因此推荐在 US2 的发现与解析完成后再做 US3。检查不依赖追溯也能独立测试
- **US4 (P2)**: 依赖 US1 的差异和 US3 的检查结果。没有 US2 时，需求关联留空而不是编造
- **US5 (P2)**: 依赖 US3 的测试检查。与 US4 可并行
- **US6 (P2)**: 依赖 US1–US3 的静态结果。不得成为静态模式的前提
- **US7 (P3)**: 依赖 US3 的确定性失败和 US6 的假设标记。没有 US6 时，严格策略只评估确定性发现

### Within Each User Story

- 该故事的测试先写并且失败
- 模型或解析先于审核服务
- 服务先于命令集成
- 故事达到 Checkpoint 后再进入下一优先级

### Parallel Opportunities

- T003 与 T004 可并行
- T005、T006、T007 可并行
- T015、T016、T017 可并行
- T020 与 T021 可并行
- T024、T025、T026 可并行
- T031、T032、T033 可并行
- T039 与 T040 可并行
- T048 与 T049 可并行
- US4 与 US5 在 US3 完成后可由不同人并行
- T057、T058、T059、T060 可并行

---

## Parallel Example: User Story 1

```bash
# 先同时写 US1 的失败测试：
Task: "T015 tests/unit/test_git_readonly.py"
Task: "T016 tests/unit/test_report_contract.py"
Task: "T017 tests/integration/test_us1_report.py"

# 测试失败后，报告的两种写出可并行：
Task: "T020 src/specguard/report/markdown.py"
Task: "T021 src/specguard/report/json_report.py"
```

## Parallel Example: User Story 2

```bash
Task: "T024 tests/unit/test_openspec_parser.py"
Task: "T025 tests/unit/test_traceability.py"
Task: "T026 tests/integration/test_us2_requirements.py"
```

## Parallel Example: User Story 3

```bash
Task: "T031 tests/unit/test_check_runner.py"
Task: "T032 tests/unit/test_java_project.py"
Task: "T033 tests/integration/test_us3_static_checks.py"
```

## Parallel Example: User Story 4

```bash
Task: "T039 tests/unit/test_risk_review.py"
Task: "T040 tests/unit/test_finding_normalization.py"
```

## Parallel Example: User Story 5

```bash
Task: "T044 tests/unit/test_test_adequacy.py"
```

## Parallel Example: User Story 6

```bash
Task: "T048 tests/unit/test_llm_client.py"
Task: "T049 tests/unit/test_secret_redaction.py"
```

## Parallel Example: User Story 7

```bash
Task: "T054 tests/unit/test_policy.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. **STOP and VALIDATE**: 按 US1 的 Independent Test 检查报告和只读边界
5. 此时还没有需求追溯和构建检查。报告必须把这些标成不可用，而不是通过

### Incremental Delivery

1. Setup + Foundational → 配置校验可独立运行
2. US1 → 可核查报告（MVP）
3. US2 → 需求与任务缺口进入同一份报告
4. US3 → 静态模式的确定性检查完成，辅助维度保持跳过
5. US4 与 US5 → 风险排序和测试有效性
6. US6 → 内网辅助审查
7. US7 → 显式严格策略。默认配置保持 `advisory`，不安装合并门禁
8. Phase 10 按 quickstart.md 做静态模式抽查

### Parallel Team Strategy

1. 一起完成 Setup 和 Foundational
2. 之后一人做 US1
3. US1 完成后，一人做 US2，另一人准备 US3 的测试；US3 的集成等 US2 的解析落地后收口
4. US3 完成后，US4 与 US5 并行
5. US6 与 US7 按顺序收口，避免模型假设在策略规则完成前被当成阻断

---

## Notes

- [P] 表示不同文件且不依赖未完成任务
- 故事标签用于追溯，设置阶段和基础阶段没有故事标签
- 每个故事都能在自己的 Checkpoint 单独验证
- 先确认测试失败，再写实现
- 不得通过删除测试、削弱断言或忽略失败来勾选任务
- 证据不足不得写成代码一定有错；检查未发现问题不得写成代码安全

---

## Phase 11: Convergence

- [X] T062 CRITICAL：在执行构建或测试时，把“这些命令可能生成文件并执行项目自带脚本”写进报告限制说明 per Constitution 安全与范围 (partial)
- [X] T063 把 `detect_project` 识别到的构建模块写入 Markdown 和 JSON 报告，不得只留在内存里 per US3/AC6 (partial)
- [X] T064 当关联测试只有不能验证该需求的简单断言时，保持需求证据为 `insufficient`，并生成指向该测试和需求的 `test_adequacy` 发现 per US5/AC4 (partial)
- [X] T065 遮盖送审内容后，把遮盖次数和位置类别写入报告，且不写入密钥原文 per US6/AC5 (partial)
- [X] T066 对状态流转、空值与空输入、事务边界、并发和授权做证据化审核；上下文不可用时写入限制，且没有失败路径时不得标成已确认缺陷 per FR-021 (partial)
- [X] T067 评估公开接口、调用方、数据保存、依赖和配置变化，并区分已核实的不兼容与假设 per FR-026 (partial)
- [X] T068 在 `include_main_specs` 为真时解析长期规范内容并纳入审核上下文，而不是只记录文件路径 per FR-006 (partial)
- [X] T069 读取测试命令实际产出的结果；没有结果或覆盖率时，在报告中标明覆盖率分析不可用，且不写入百分比 per FR-025 (partial)
- [X] T070 在人类可读报告中写明含糊需求的 `ambiguity_reason` per US2/AC4 (partial)
- [X] T071 在辅助审查可得时，把已配置的服务标识和模型标识写入报告 per US6/AC1 (partial)

---

## Phase 12: Convergence

- [X] T072 模型返回非成功状态或无法作为审核结果使用时，把四个辅助维度标为 `ERROR`，并保留已完成的确定性检查 per US6/AC3 (partial)
- [X] T073 只对已配置的内部主机做有限次重试，并用 `api_key_env` 指向的环境变量认证，且不把密钥写入报告 per plan: llm client (partial)
- [X] T074 仅当 `report.include_source_snippets` 为真时写入已经遮盖的短源码片段；关闭时报告不包含源码摘录 per plan: report contract (partial)

---

## Phase 13: Convergence

- [X] T075 在 Markdown 的潜在风险中写出失败路径；没有失败路径时标明不可用，不得编造 per US4/AC1 (partial)
- [X] T076 在 Markdown 的检查结果中写出有限度的诊断摘要，并与 JSON 中的 `diagnostic` 一致 per plan: report contract (partial)

---

## Phase 14: Convergence

- [X] T077 在 Markdown 的证据定位中写明已有发现的文件和行；没有位置时标明不可用，不得编造行号 per US1/AC6 (partial)

---

## Phase 15: 安装命令

**Purpose**: 使用者安装 `specguard` 命令后，在被审核仓库里运行。不把 SpecGuard 源码克隆进该仓库。v0.1 交付 Python 控制台脚本，不要求原生二进制。

**Independent Test**: 在一个不含 `src/specguard` 的目录里执行已安装的 `specguard version`，命令可用且不要求当前目录是 SpecGuard 源码检出。

- [X] T078 在 `tests/unit/test_install_entry.py` 中编写失败测试：`pyproject.toml` 的 `[project.scripts]` 将 `specguard` 指向 `specguard.cli.main:app`；`docs/install.md` 写明使用者安装命令后在被审核仓库运行、不克隆 SpecGuard 源码，并且 v0.1 不要求原生二进制
- [X] T079 在 `pyproject.toml` 中保留控制台脚本 `specguard = "specguard.cli.main:app"`，不添加原生二进制打包配置
- [X] T080 [P] 在 `docs/install.md` 中写明使用者把 `specguard` 安装到命令路径，再到被审核的 Java 仓库运行；该仓库不包含 SpecGuard 源码。开发者才在本仓库源码检出中测试

---

## Phase 16: Convergence

- [X] T081 把 `docs/install.md` 的安装命令改为 `uv tool install "git+https://github.com/sl903dj/SpecGuard"`，并写明用源码绝对路径执行 `uv tool install --force` 后，在不含 `src/specguard` 的目录运行 `specguard version`；不得再写 `uv tool install specguard`。同步更新 `tests/unit/test_install_entry.py` per plan: GitHub install (contradicts)
- [X] T082 在仓库根目录添加 Apache-2.0 标准文本 `LICENSE`，版权行写 `Copyright 2026 sl903dj`，并把 `pyproject.toml` 的 `license` 设为 `Apache-2.0` per plan: Apache-2.0 license (missing)
- [X] T083 添加中文 `README.md` 和英文 `README.en.md`，文首互相链接，写明只读质量门、GitHub 安装、本地 `specguard version` 验证，并链接 `LICENSE`；不得把产品写成编程助手或默认合并门禁 per plan: bilingual README (missing)

---

## Phase 17: 内网离线安装

**Purpose**: 不能访问 GitHub 或 PyPI 的内网电脑，使用外网取得并手工传入的源码和依赖轮子，完全离线安装 `specguard`。

**Independent Test**: `docs/install.md` 列出直接依赖并给出 `uv tool install --offline --no-index --find-links`；中英文 README 指向该节。安装过程不要求内网电脑访问 `github.com` 或 `pypi.org`。

- [X] T084 在 `tests/unit/test_install_entry.py` 中编写失败测试：`docs/install.md` 写明外网克隆 `https://github.com/sl903dj/SpecGuard.git`、手工传入源码和轮子目录，并列出直接依赖 `typer>=0.12`、`pydantic>=2`、`httpx>=0.27`、`pyyaml>=6`，同时说明传递依赖随轮子目录传入、`pytest` 不是安装命令所需；内网命令包含 `uv tool install --offline --no-index --find-links`。`README.md` 与 `README.en.md` 指向 `docs/install.md` 的离线安装说明
- [X] T085 在 `docs/install.md` 中按 `specs/001-specguard-quality-gate/quickstart.md` 写明外网准备（`uv lock`、`uv export --frozen --no-dev --no-emit-project`、用临时环境的 `pip download` 生成轮子目录）和内网命令 `uv tool install --offline --no-index --find-links <轮子目录> <源码目录>`。列出 `typer>=0.12`、`pydantic>=2`、`httpx>=0.27`、`pyyaml>=6`，写明传递依赖必须在轮子目录中，内网机预先具备 Python 3.11+ 和 `uv`，安装时不访问 `github.com` 或 `pypi.org`
- [X] T086 [P] 在 `README.md` 和 `README.en.md` 中指向 `docs/install.md` 的离线安装节，保留能访问 GitHub 时的 `uv tool install "git+https://github.com/sl903dj/SpecGuard"`
