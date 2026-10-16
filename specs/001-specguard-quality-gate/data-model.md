# Data Model: SpecGuard 变更质量守卫

一次审核的对象都在内存中。本文件描述字段、关系和状态，不描述数据库表。报告写出的 JSON 与这里的模型一致，契约见 [contracts/report.md](contracts/report.md)。

## ReviewSubject

一次被审核的代码变更。

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| repository_root | 版本库根目录 | 审核开始前必须解析成功 |
| base_revision | 请求的基线 | 无法解析则整次审核停止 |
| target_revision | 请求的目标 | 默认当前 `HEAD` |
| resolved_base | 实际解析出的基线 | 必须写入报告，不得悄悄替换 |
| resolved_target | 实际解析出的目标 | 必须写入报告 |
| head_sha | 开始时的提交标识 | 结束时再次读取，不一致则报告不完整 |
| worktree_state | 开始时的工作区指纹 | 仅在明确纳入未提交改动时使用 |
| includes_uncommitted | 是否纳入未提交改动 | 默认否 |
| changed_files | 变更文件列表 | 见 ChangedFile |

## ChangedFile

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| path | 当前路径 | 删除文件保留旧路径 |
| previous_path | 重命名前路径 | 非重命名时为空 |
| change_type | `added`、`modified`、`deleted`、`renamed` | 必须来自 Git，不能猜测 |
| line_ranges | 变更行范围 | 无法精确到行时为空，并在证据里说明 |
| committed | 该变更是否已提交 | 与工作区变更分开 |

## ChangeSelection

所选 OpenSpec 变更。

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| name | 变更目录名 | 多个进行中变更且未选择时不得自动填充 |
| artifacts | 找到和缺失的工件 | 至少报告 proposal、design、tasks、delta specs |
| requirements | 需求条目 | 见 Requirement |
| tasks | 任务项 | 见 TaskItem |
| available | 是否找到 OpenSpec 根 | 为否时需求审核不可用 |

## Requirement

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| identifier | 稳定标识 | 由变更名、变更语义和标题组成 |
| title | 需求标题 | 保留原文 |
| change_semantics | `added`、`modified`、`removed` | 删除不等于实现缺陷 |
| scenarios | 场景文本和行号 | 可为空 |
| source | 文件路径和行号 | 必须保留 |
| ambiguous | 是否信息不足 | 为真时进入人工审核 |
| ambiguity_reason | 缺什么信息 | `ambiguous` 为真时必填 |
| evidence | 关联证据 | 见 Evidence |

## TaskItem

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| identifier | 任务标识 | 保留清单中的编号 |
| text | 任务原文 | |
| marked_complete | 是否勾选完成 | 没有勾选标记时为否，不猜测 |
| source | 文件和行号 | |
| support | `code`、`test`、`both`、`none` | 完成后仍为 `none` 时形成完整性缺口 |
| evidence | 支撑证据 | 没有支撑时状态为 `insufficient` |

## Evidence

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| status | `direct`、`inferred`、`insufficient` | 必填 |
| requirement_id | 相关需求 | 可空 |
| task_id | 相关任务 | 可空 |
| file | 文件路径 | 没有位置时为空 |
| line_start / line_end | 行范围 | 不知道时为空，禁止填伪造行号 |
| check_id | 来源检查 | 可空 |
| note | 为什么是这一级证据 | 推断和不足时必填 |

文件重叠只能产生 `inferred`。没有任何关联时使用 `insufficient`，并且不得把对应需求或任务标成实现错误。

## CheckResult

一次确定性检查。

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| check_id | 如 `build`、`tests`、`checkstyle` | 来自配置的检查名 |
| required | 是否必需 | |
| status | 见下方状态 | 必填且只能有一个 |
| command | 实际命令 | 未执行时为空 |
| duration_seconds | 耗时 | 未执行时为空 |
| exit_code | 进程退出码 | 未执行时为空 |
| diagnostic | 有长度上限的摘要 | 失败、错误、超时时保留 |
| tool_version | 可得的工具版本 | 不可得时为空 |

### 检查状态

```text
未开始 → PASS
       → FAIL
       → SKIPPED
       → ERROR
       → TIMEOUT
```

状态一旦写出就不再改成另一种成功。`SKIPPED`、`ERROR`、`TIMEOUT` 都不能显示为 `PASS`。必需检查落入后三者时，整次审核为 `REVIEW_INCOMPLETE`。

## Finding

归一后的一条发现。确定性检查和辅助审查使用同一个模型。

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| finding_id | 报告内稳定标识 | 按类别、路径、行、来源排序后生成，不随机 |
| category | `requirements`、`task_integrity`、`business_logic`、`test_adequacy`、`regression` | |
| severity | `critical`、`high`、`medium`、`low`、`info` | |
| summary | 一句话结论 | |
| failure_path | 说得通的输入或执行路径 | 业务逻辑疑点没有该字段时不得写成缺陷 |
| evidence_status | `confirmed`、`hypothesis`、`insufficient` | 模型输出默认 `hypothesis` |
| origin | 检查名或审查阶段 | 必填 |
| location | 文件和行，或“位置不可用” | 禁止伪造 |
| related_requirement_ids | 需求标识 | 可空 |
| related_task_ids | 任务标识 | 可空 |
| duplicate_group | 可能重复的组 | 合并展示时仍保留原始来源 |

冲突的发现都保留，并列入报告的冲突列表。不得合成一个折中结论。

## ReviewPolicy

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| mode | `advisory` 或 `strict` | 默认 `advisory` |
| block_on | 可阻断的严重程度 | 只作用于确定性失败 |
| llm_findings_block | 模型假设是否阻断 | v0.1 固定为否 |
| blocked | 是否 `POLICY_BLOCKED` | 建议模式恒为否 |

严格模式下，只有 `evidence_status = confirmed` 且严重程度在 `block_on` 中的确定性失败才使 `blocked` 为真。必需检查未完成时优先标成 `REVIEW_INCOMPLETE`，不把缺失检查算成通过，也不把它伪装成一次干净的阻断。

## ReviewReport

| 字段 | 说明 | 规则 |
| --- | --- | --- |
| schema_version | 报告结构版本 | v0.1 使用 `1.0` |
| review_status | `REVIEW_COMPLETE`、`REVIEW_INCOMPLETE`、`POLICY_BLOCKED` | 见下方整次状态 |
| metadata | 版本、变更、配置版本、工具版本、起止时间 | 可得的都必须记录 |
| summary | 人工审核提示、覆盖计数、最高风险、可靠检查 | 最高风险排在前面 |
| disclaimer | 固定限制说明 | 必须出现在两份报告中 |
| requirements / tasks / checks / findings | 上列对象的列表 | 两份报告内容相同 |

### 整次审核状态

```text
检查尚未结束 → REVIEW_INCOMPLETE
全部必需检查有明确结果，且没有策略阻断 → REVIEW_COMPLETE
全部必需检查有明确结果，且严格策略命中确定性失败 → POLICY_BLOCKED
```

`REVIEW_COMPLETE` 仍可以包含发现。没有任何发现时，报告列出实际执行的检查，并声明这不是“代码没有缺陷”。

## 关系

- 一个 ReviewSubject 选择零个或一个 ChangeSelection。没有选择结果时，需求相关章节标为不可用。
- 一个 ChangeSelection 包含多条 Requirement 和多个 TaskItem。
- Requirement 和 TaskItem 各有零条或多条 Evidence。
- CheckResult 可以成为 Evidence 的来源，也可以单独出现在报告中。
- Finding 引用零个或多个 Requirement、TaskItem、ChangedFile 和 CheckResult。
- ReviewPolicy 根据 CheckResult 和 Finding 计算 ReviewReport 的整次状态。
