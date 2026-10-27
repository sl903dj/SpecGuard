# Data Model: 补齐质量门的证据与对照能力

本功能扩展 v0.3 的需求、场景、发现和报告元数据。未列出的字段保持 [004 数据模型](../004-gate-initial-openspec/data-model.md) 的约束。报告结构版本为 `1.3`。

## EvidenceScope

`range | target_tree`

- `range`：证据文件是选定基线到目标版本的差异，外加明确纳入的未提交文件。删除文件不提供内容证据。
- `target_tree`：证据文件是目标版本树中的路径。内容读取该版本，不读取工作区里比该版本更新的副本。仅 OpenSpec 当前规范可用。

关系：证据范围决定追溯和场景覆盖能读哪些文件。风险检查仍只看差异文件。

## Scenario 扩展

在现有名称和来源行上增加：

- `body`：场景标题之后、下一条场景或需求结束之前的正文。没有正文时为空字符串。

OpenSpec 与 Spec Kit 都保存正文。空正文不能产生 `supported`。

## RequirementEvidence

不新增需求状态枚举。每条需求的主证据仍是列表中的一条：

| 状态 | 条件 | 说明 |
| --- | --- | --- |
| `direct` | 证据范围内文件含需求标识 | 只代表找到关联，不代表验收场景已经通过 |
| `inferred` | 仅文件名或路径出现在标题或正文 | 不能单独证明需求已经实现 |
| `insufficient` | 没有以上线索 | 找不到实现证据 |

一条需求不得同时保留两种主状态。场景结果不回写这条证据。

## ScenarioAssessment

- `requirement_id`
- `scenario_name`：没有场景时为空
- `status`：`supported | gap | unavailable`
- `test_file`、`test_line`：只有 `supported` 时出现，且行号大于 0
- `note`：`gap` 与 `unavailable` 必须说明原因

关系：一条需求有零到多条场景。没有场景时恰好一条 `unavailable`。有场景时每条场景恰好一条 `supported` 或 `gap`。辅助审查发现不能成为评估来源。

## ConsistencyItem

仅在所选对象是 OpenSpec 变更时出现。

- `capability`
- `current_requirement_id`、`current_file`、`current_line`
- `change_requirement_id`、`change_file`、`change_line`
- `status`：`conflict | human_review`
- `summary`

关系：当前规范需求不加入 `requirements`。`conflict` 必须两边都有真实行号。`modified` 或 `removed` 的已声明增量不产生条目。不同能力的同名标题不配对。

## CalibrationRecord

工程师放在报告目录的 `calibration.json`。系统只读。

- `complete`：布尔值，默认按未完成处理
- `reviews`：历史审核列表
  - `subject_id`：非空
  - `finding_ids`：该次审核的发现编号
  - `verdicts`：`finding_id` 加 `true_issue` 或 `false_positive`
  - `misses`：漏报说明
  - `no_misses`：布尔值

一次 `reviews` 条目完整的条件：每个 `finding_ids` 恰好一个结论，结论中的编号都在列表内，同一编号没有第二种结论，并且 `no_misses` 与非空 `misses` 二者居其一。

## CalibrationView

报告中的对照结果，不是工程师的原始文件。

- `status`：`incomplete | complete`
- `completed_review_count`
- `rejected_complete_mark`
- `notes`：不可用、遮盖或无法对应的说明，不含密钥原文

`complete` 仅当原始记录声明完成且 `completed_review_count` 至少为 1。拒绝完成标记时状态仍是 `incomplete`。

## RiskDisposition

九个固定类别：`boundary`、`exception`、`null_empty`、`transaction`、`concurrency`、`authorization`、`compatibility`、`persisted_data`、`dependency_config`。

- `risk_class`：发现上的可选类别
- `disposition`：`finding | missing_context`
- `finding` 还要求真实位置和失败路径
- `evidence_status` 为 `confirmed` 的只来自空 catch、空的空值判断、集合长度上界比较
- 没有行号时不得为了填位置而使用第 1 行

## ModuleCoverage

- `changed_modules`：变更文件所在的构建模块，按路径排序
- `execution`：`repository | unrecognized | not_configured`
- `not_separately_covered`：仓库级命令没有分别执行的涉及模块

多个涉及模块且执行方式为 `repository` 时，检查列表增加 `module-separation`，状态为跳过，命令为空。该检查不是通过。

## 报告视图

`schema_version` 为 `1.3`。1.2 的 `subject_kind`、`tasks_available`、提供方和弃用别名保留。

元数据增加 `evidence_scope`、`calibration`、`module_coverage` 和 `risk_dispositions`。报告正文增加 `scenario_assessments` 与 `consistency_items`。人类可读报告和结构化报告使用同一组对象。字段详见 [contracts/report.md](contracts/report.md)。

## 状态约束

- 对照完成不改变 `policy.mode`，也不把 `blocked` 设为真。
- `strict` 仍只统计已证实、非辅助审查、且达到配置严重程度的发现。
- 对照未完成而 `strict` 已阻断时，对照视图保持 `incomplete`，并在说明中写出门禁依据不足。
