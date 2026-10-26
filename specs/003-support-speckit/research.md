# Research: Spec Kit 工件支持

## Decision 1: 采用可插拔工件提供方

**Decision**: 在核心流水线前增加中立的 `ArtifactProvider` 边界，由 OpenSpec 和 Spec Kit 适配器输出同一个 `ArtifactBundle`。

**Rationale**: 当前追溯、测试有效性、风险、策略和报告逻辑已经基于规范化需求与任务工作；隔离发现和解析差异可以保留这些能力，并防止 Spec Kit 规则继续进入 `pipeline.py`。

**Alternatives considered**:
- 在现有 `openspec` 模块增加格式分支：改动较少，但会混合两套目录、选择和语义规则。
- 将输入先转换成 OpenSpec：会伪造 Spec Kit 没有的增量语义，并引入临时文件和只读风险。

## Decision 2: 保留旧配置，新增中立 artifacts 配置

**Decision**: 继续接受版本 1 的 `openspec` 配置；新增 `artifacts.provider`、`artifacts.subject` 和 `artifacts.root`。未提供 `artifacts` 时沿用 OpenSpec；同时提供且语义冲突时校验失败。

**Rationale**: Pydantic 当前禁止未知字段，直接改名会使所有已有配置失效。显式提供方也能解决同仓库两种工件并存时的歧义。

**Alternatives considered**:
- 自动检测并固定优先 Spec Kit：会静默改变已有仓库行为。
- 配置版本直接升为 2：当前新增能力不需要强制所有用户迁移。

## Decision 3: 选择顺序为显式值、状态文件、歧义错误

**Decision**: CLI/配置显式 subject 优先；Spec Kit 未显式选择时只读 `.specify/feature.json`；没有有效状态时不按 Git 分支猜测。

**Rationale**: 当前 Spec Kit 官方工作流用 `feature_directory` 选择活动功能，并明确指出功能状态不由 Git 分支决定。遵循该规则可避免审核错误功能。

**Alternatives considered**:
- 按当前 Git 分支匹配：与 Spec Kit 当前状态模型冲突。
- 多目录时选择最新编号：不可审计，也可能把历史功能当成当前需求。

## Decision 4: Spec Kit 需求使用原始 FR 标识且无增量语义

**Decision**: `Requirement.change_semantics` 改为可空；Spec Kit 解析 `FR-\d+`，保留用户故事、优先级和验收场景。

**Rationale**: Spec Kit 的 `spec.md` 描述完整功能，不是 ADDED/MODIFIED/REMOVED 增量。空值比伪造 `added` 更诚实，并保持 OpenSpec 原值不变。

**Alternatives considered**:
- 全部标为 `added`：会触发错误的删除/修改推理。
- 增加第四个 `full` 枚举：仍把两个不同概念塞进同一字段。

## Decision 5: 上下文文档不作为实现证据

**Decision**: `plan.md`、`research.md`、`data-model.md`、`contracts/`、`quickstart.md` 和 `checklists/` 登记为 `ContextDocument`，可进入受限辅助审查上下文，但不直接提升需求或任务证据等级。

**Rationale**: 设计意图不能证明代码已经实现。该规则符合宪章“结论必须有证据”。

**Alternatives considered**:
- 把计划或任务文字当直接证据：会把自我声明误当实现事实。
- 完全忽略上下文：会降低风险审查和人工复核价值。

## Decision 6: 内置结构校验，不假设 speckit validate

**Decision**: 首版校验目录边界、JSON 状态、必需文件、稳定 ID、重复 ID和模板占位符；不新增任意外部 Spec Kit 命令。

**Rationale**: GitHub Spec Kit 当前没有与 `openspec validate` 对等的稳定统一命令。内置只读校验可复现，也不扩大命令白名单。

**Alternatives considered**:
- 调用 Agent slash command：不是可依赖的项目命令，且可能产生写入。
- 运行用户配置的任意校验命令：违反可信命令允许列表原则。

## Decision 7: 报告契约升到 1.1 并保留弃用别名

**Decision**: 增加 `artifact_provider`、`subject_id`、`selection_source` 和上下文清单；报告 schema 升至 `1.1`。`metadata.change` 与 `artifacts.selected_change` 在兼容期继续输出。

**Rationale**: 新字段改变公共结构，应显式版本化；保留旧字段可给 OpenSpec 消费者迁移窗口。

**Alternatives considered**:
- 保持 `1.0` 并静默加字段：违反稳定结构承诺。
- 立即删除旧字段：不符合并存和兼容目标。

## Decision 8: 测试采用提供方契约测试加端到端回归

**Decision**: 为两种提供方运行同一组发现、选择、加载契约测试；新增 Spec Kit 夹具，并保留全部 OpenSpec 回归。

**Rationale**: 共享契约能锁住抽象边界，端到端测试能证明报告一致性和只读性质。

**Alternatives considered**:
- 只测解析函数：无法发现配置、选择、流水线和报告之间的集成错误。
