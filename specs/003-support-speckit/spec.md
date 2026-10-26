# Feature Specification: Spec Kit 工件支持

**Feature Branch**: `003-support-speckit`
**Created**: 2026-10-26
**Status**: Draft
**Input**: “在现有 OpenSpec 支持之外，让 SpecGuard 支持审核 GitHub Spec Kit 的规格、计划和任务工件。”

## User Scenarios & Testing

### User Story 1 - 审核一个 Spec Kit 功能 (Priority: P1)

使用 Spec Kit 管理需求的工程师，希望直接用 SpecGuard 审核 `specs/<feature>/` 下的功能规格，而不必把工件转换为 OpenSpec。报告需要读取功能需求、验收场景和任务，并把它们与 Git 变更及测试证据关联。

**Independent Test**: 对包含 `spec.md`、`plan.md` 和 `tasks.md` 的样例仓库运行审核；报告应列出 `FR-*` 需求、`T*` 任务、来源行和证据状态。

**Acceptance Scenarios**:

1. **Given** 已显式配置 Spec Kit 提供方和功能目录，**When** 审核开始，**Then** 系统读取该目录中的 `spec.md`、`plan.md` 和 `tasks.md`，并记录找到及缺失的工件。
2. **Given** `spec.md` 含 `FR-001` 及验收场景，**When** 报告生成，**Then** 需求保留原始标识、来源行、用户故事和场景，不被伪装成 OpenSpec 的新增、修改或删除需求。
3. **Given** `tasks.md` 含 `[X] T001 [P] [US1] ...`，**When** 审核任务完整性，**Then** 系统保留任务标识、完成状态、并行标记和用户故事关联，并检查代码或测试支撑。
4. **Given** `research.md`、`data-model.md`、`contracts/`、`quickstart.md` 或 `checklists/` 存在，**When** 工件被加载，**Then** 它们作为设计或验证上下文登记，不被误当成需求或实现任务。

---

### User Story 2 - 可靠选择 Spec Kit 审核对象 (Priority: P1)

一个仓库可能包含多个 Spec Kit 功能目录。工程师需要清楚知道本次审核使用了哪个功能，系统不能仅凭当前 Git 分支静默猜测。

**Independent Test**: 准备两个功能目录，分别验证显式选择、`.specify/feature.json` 选择、状态文件无效和未选择四种情况。

**Acceptance Scenarios**:

1. **Given** 配置或命令行显式指定功能目录，**When** 审核开始，**Then** 显式值优先于 `.specify/feature.json`。
2. **Given** 没有显式选择且 `.specify/feature.json` 含有效 `feature_directory`，**When** 审核开始，**Then** 系统选择该目录并在报告记录选择来源。
3. **Given** 状态文件指向不存在、越界或不含 `spec.md` 的目录，**When** 审核开始，**Then** 系统在执行构建、测试或辅助审查前停止，并给出可操作错误。
4. **Given** 存在多个功能目录但没有显式选择或有效状态，**When** 审核开始，**Then** 系统要求选择，不按 Git 分支名任意匹配。

---

### User Story 3 - 保持 OpenSpec 用户兼容 (Priority: P1)

已有 OpenSpec 用户升级后，应继续使用当前配置和审核流程。Spec Kit 支持是新增工件提供方，而不是替换或重新解释 OpenSpec。

**Independent Test**: 使用当前 OpenSpec 单变更和多变更夹具运行完整回归；配置、选择、需求语义和报告结论与新增支持前一致。

**Acceptance Scenarios**:

1. **Given** 现有配置只含 `openspec` 节，**When** 升级后运行审核，**Then** 系统按 OpenSpec 兼容模式加载，不要求新增字段。
2. **Given** 用户显式选择 OpenSpec，**When** 仓库同时含 OpenSpec 和 Spec Kit 工件，**Then** 只加载 OpenSpec 工件。
3. **Given** 新旧配置同时对审核对象给出冲突选择，**When** 校验配置，**Then** 系统在检查开始前拒绝并指出冲突字段。
4. **Given** 使用旧 `--change` 参数，**When** OpenSpec 审核开始，**Then** 参数保持原语义；它不得被静默解释成 Spec Kit 功能目录。

---

### User Story 4 - 在报告中区分工件来源 (Priority: P2)

审核工程师和后续工具需要知道结论来自 OpenSpec 还是 Spec Kit，并能稳定定位审核对象和工件。

**Independent Test**: 分别生成 OpenSpec 与 Spec Kit 的 Markdown/JSON 报告，验证两者记录提供方、审核对象、选择来源和工件清单，且需求与任务统计一致。

**Acceptance Scenarios**:

1. **Given** 任一工件提供方完成加载，**When** 报告生成，**Then** 报告明确记录 `artifact_provider`、中立的 `subject_id` 和选择来源。
2. **Given** Spec Kit 功能缺少 `plan.md` 或 `tasks.md`，**When** 报告生成，**Then** 缺失项按 Spec Kit 规则报告，不出现 OpenSpec 专属的 `proposal.md` 或增量 `specs/` 缺失提示。
3. **Given** Spec Kit 需求没有增量语义，**When** 结构化报告生成，**Then** 语义字段为空或明确为不适用，不伪造 `added`。
4. **Given** 报告契约新增字段，**When** 版本发布，**Then** 结构化报告使用明确的新次版本，并在兼容期保留旧 OpenSpec 字段作为弃用别名。

### Edge Cases

- `.specify/feature.json` 不是合法 JSON、缺少 `feature_directory` 或包含非字符串值。
- 功能目录在仓库外，或经符号链接逃出仓库；审核必须拒绝。
- `spec.md` 仍含模板占位符、重复 `FR-*`、缺失需求 ID或重复任务 ID。
- `tasks.md` 使用大小写不同的完成标记、没有 `[USn]`、含阶段标题或依赖说明。
- 同时存在 OpenSpec 和 Spec Kit 工件但配置未说明提供方。
- Spec Kit 只有 `spec.md`，尚未完成计划或任务阶段。
- 工件包含中文、CRLF 或无法按 UTF-8 严格解码的内容。

## Requirements

### Functional Requirements

- **FR-001**: 系统必须新增 `speckit` 工件提供方，并与现有 `openspec` 提供方并存。
- **FR-002**: 系统必须把工件发现、对象选择和工件加载抽象为提供方边界；核心追溯、风险、测试、策略和报告流水线不得直接依赖 OpenSpec 目录结构。
- **FR-003**: 现有仅含 `openspec` 节的版本 1 配置必须继续有效，并保持原有默认行为。
- **FR-004**: 新配置必须允许显式选择 `openspec` 或 `speckit`；自动模式同时发现两类工件时必须报歧义，不得静默选择。
- **FR-005**: Spec Kit 审核对象选择顺序必须是命令行或配置中的显式值优先，其次是 `.specify/feature.json` 的 `feature_directory`；不得把 Git 分支名作为隐式选择依据。
- **FR-006**: 系统必须验证 Spec Kit 功能目录存在、位于仓库允许范围内且包含 `spec.md`，无效时在任何检查或网络调用前停止。
- **FR-007**: 系统必须从 `spec.md` 解析稳定的 `FR-*` 标识、需求正文、来源行、用户故事、优先级和验收场景。
- **FR-008**: 系统必须从 `tasks.md` 解析 `T*` 标识、完成状态、`[P]` 标记、`[USn]` 关联、正文和来源行。
- **FR-009**: 重复需求或任务标识、未替换的关键模板占位符必须形成明确错误或限制，不得静默合并。
- **FR-010**: `plan.md` 和可选的 `research.md`、`data-model.md`、`contracts/`、`quickstart.md`、`checklists/` 必须作为上下文工件登记；不得当作实现完成证据。
- **FR-011**: Spec Kit 核心工件完整性必须分别报告 `spec.md`、`plan.md` 和 `tasks.md`；只有 `spec.md` 时允许需求审核，但必须说明计划或任务能力不可用。
- **FR-012**: 规范化需求模型必须允许“无增量语义”；Spec Kit 需求不得被标成 OpenSpec 的 `added`、`modified` 或 `removed`。
- **FR-013**: 规范化工件结果必须包含提供方、审核对象标识、选择来源、找到和缺失的工件、需求、任务及上下文文档。
- **FR-014**: 现有需求追溯、任务完整性、测试有效性、风险、策略和报告逻辑必须复用规范化结果，并保持证据规则不变。
- **FR-015**: CLI 必须提供中立的审核对象参数；旧 `--change` 必须保留为 OpenSpec 兼容参数。两者冲突时必须在检查前报错。
- **FR-016**: Markdown 和 JSON 报告必须记录工件提供方、中立审核对象和选择来源；两种格式的需求数、任务缺口和工件清单必须一致。
- **FR-017**: 结构化报告的契约变更必须提升次版本；兼容期内必须保留 `metadata.change` 和 `artifacts.selected_change` 作为 OpenSpec 旧字段，并标记弃用。
- **FR-018**: Spec Kit 工件不得被审核过程修改；读取 `.specify/feature.json` 不得改写该文件。
- **FR-019**: 辅助审查使用 Spec Kit 上下文时必须继续执行长度限制、密钥遮盖和不可信内容隔离。
- **FR-020**: 所有现有 OpenSpec 单元与集成场景必须继续通过，并新增 Spec Kit 发现、解析、选择、追溯、报告和只读测试。

### Key Entities

- **Artifact Provider（工件提供方）**: 定义工件发现、对象选择、加载和可选验证规则；首批值为 `openspec` 与 `speckit`。
- **Artifact Subject（审核对象）**: 一次需求审核所针对的 OpenSpec 变更或 Spec Kit 功能目录，包含中立标识和选择来源。
- **Artifact Bundle（工件包）**: 提供方加载后的规范化结果，包含工件清单、需求、任务、上下文和限制。
- **Context Document（上下文文档）**: 计划、研究、数据模型、契约、快速开始或检查清单，只帮助理解，不直接证明实现完成。
- **Requirement（需求）**: 保留来源提供方的稳定标识；增量语义对 Spec Kit 可为空。
- **Task Item（任务项）**: 保留完成状态、并行标记、用户故事关联和证据。

## Success Criteria

- **SC-001**: 对标准 Spec Kit 样例，100% 的 `FR-*` 和 `T*` 条目以原始标识和正确来源行出现在报告中。
- **SC-002**: 在显式选择、状态文件选择、歧义和非法路径四组场景中，审核对象选择结果 100% 符合优先级规则，且错误场景不执行构建、测试或模型调用。
- **SC-003**: 当前 OpenSpec 自动化测试全部保持通过；既有版本 1 配置无需修改即可运行。
- **SC-004**: Spec Kit 报告中被错误标记为 `added/modified/removed` 的需求数量为 0。
- **SC-005**: Markdown 与 JSON 报告的提供方、审核对象、需求总数、任务缺口和缺失工件完全一致。
- **SC-006**: 审核前后 Spec Kit 工件、`.specify/feature.json`、Git 索引和提交历史保持不变。

## Assumptions

- 本功能支持 GitHub Spec Kit 当前标准工件布局：项目根含 `.specify/`，功能工件位于 `specs/<feature>/`。
- Spec Kit 没有与 `openspec validate` 完全对等且稳定的统一验证命令，因此首版以内置结构校验为主。
- “兼容 OpenSpec”指旧配置、CLI 语义和审核结论继续工作；结构化报告因新增提供方元数据提升次版本，并提供弃用字段过渡。
- 本功能不改变 SpecGuard 对 Java 服务端、只读审核、建议模式和内网辅助审查的既有范围。
