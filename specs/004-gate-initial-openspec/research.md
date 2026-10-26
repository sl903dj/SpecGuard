# Research: 从零开始的 OpenSpec 质量门

## Decision 1: 当前规范是 OpenSpec 的第二种对象，不是新提供方

**Decision**: 继续使用 `provider: openspec`。对象种类为 `current`（`openspec/specs/`）或 `change`（`openspec/changes/<名称>/`）。Spec Kit 仍由 `speckit` 提供方处理。

**Rationale**: 两类工件都属于 OpenSpec，只是需求来源不同。再加一个提供方会让 `auto` 在同一目录下看到两个 OpenSpec 来源。

**Alternatives considered**:

- 新增 `provider: openspec-baseline`：配置和自动识别都会把同一套 OpenSpec 根目录算成两种提供方。
- 把当前规范伪装成一个名为 `current` 的变更目录：会进入增量解析，并可能与真实变更重名。

## Decision 2: 主规范需求不进入 ADDED/MODIFIED/REMOVED

**Decision**: 只接受 `openspec/specs/<能力>/spec.md` 里、不位于增量标题下的 `### Requirement:`。标识为 `<能力>:<标题 slug>`，`change_semantics` 为 `null`。能力名称和来源行单独保留。文件若只含 ADDED、MODIFIED 或 REMOVED，视为放错位置的变更，在检查前报错。

**Rationale**: 规格禁止因为“没有旧规范”而编造增量语义。现有变更解析依赖这三组标题，主规范沿用 OpenSpec 的普通 Requirement 标题。

**Alternatives considered**:

- 把全部主规范需求标成 `added`：直接违反规格。
- 只保留标题、不给稳定标识：报告无法逐条对应来源。

## Decision 3: 选择规则按对象是否并存分叉

**Decision**:

- 只有进行中的变更：保持今天的规则。一个变更自动选择，多个变更要求 `--change` 或配置中的变更名。
- 只有当前规范：选择 `current`，不要求变更名。
- 两者都有且未显式选择：在检查前失败。
- `--baseline` 选择当前规范。它与 `--change`、配置中的变更名冲突时失败。
- 第一份规范若位于 `changes/`，只有显式选择该变更时才按变更加载，不会被当成当前规范。

**Rationale**: 常见仓库同时有已接受规范和一份进行中变更。自动沿用“唯一变更”会把整份规范排除在外，也可能让工程师误以为审核覆盖了整个系统。失败关闭符合规格，且一旦显式选择变更，增量行为不变。

**Alternatives considered**:

- 两者并存时仍自动选择唯一变更：升级后会静默忽略当前规范，与规格冲突。
- 两者并存时合并需求和变更：一次报告会混入两套范围。

## Decision 4: 证据范围继续使用 Git 差异

**Decision**: 复用现有版本范围收集。只有该范围内的文件可以支撑需求。基线中已有、但目标差异未包含的文件不得算作证据。不新增整库扫描。

**Rationale**: 规格把证据限制在工程师选定的版本范围，并明确范围外代码不能证明需求已实现。

**Alternatives considered**:

- 对当前规范扫描整个目标树：能回答“整库是否符合规范”，但把未纳入本次范围的历史代码算成证据，违反规格。

## Decision 5: 任务缺失是不可用，不是零缺口

**Decision**: 当前规范不读取变更任务，也不在 `openspec/specs/` 下发明任务文件。`tasks_available` 为 `false` 时，Markdown 写明任务完整性不可用，JSON 不把 `task_gap_count: 0` 解释成任务通过。变更对象仍按原任务清单计算缺口。

**Rationale**: 零缺口会被读成“任务都有支撑”。当前规范通常没有任务清单。

**Alternatives considered**:

- 把相邻变更的 `tasks.md` 借给当前规范：把另一次变更的任务算进整份规范。

## Decision 6: 报告契约升到 1.2

**Decision**: `schema_version` 改为 `1.2`，增加 `subject_kind`（`current`、`change`、`feature`）和 `tasks_available`。保留 1.1 的提供方、`subject_id`、`selection_source` 和弃用别名。当前规范的 `metadata.change` 与 `artifacts.selected_change` 为空，`subject_id` 为 `current`。

**Rationale**: 对象种类是新的报告事实。沿用 `metadata.change` 会让消费者把当前规范误认为某个变更。

**Alternatives considered**:

- 只在 Markdown 里加一句话：JSON 消费者仍无法区分对象。
- 把 `current` 写入 `metadata.change`：旧字段会重新变成有含义的选择结果。
