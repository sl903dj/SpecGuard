# Contract: 审核报告

一次审核从一个内存中的 [ReviewReport](../data-model.md) 生成 Markdown 和 JSON。两者的结论、证据、检查结果和限制说明必须一致。JSON 的 `schema_version` 在 v0.1 中为 `"1.0"`。增加必填字段时升结构版本，不静默改变旧字段含义。

## Markdown 必含章节

1. 标题与整次状态：`REVIEW_COMPLETE`、`REVIEW_INCOMPLETE` 或 `POLICY_BLOCKED`。
2. **需要人工审核**：含糊需求、证据不足、模型假设和冲突结论。
3. **需求覆盖**：有直接证据、仅有推断、证据不足的需求计数；任务完整性缺口另计。
4. **潜在风险**：按严重程度排列。每条包含位置、说得通的失败路径和证据状态。
5. **证据定位**：能连到需求条目、变更文件、代码行、测试结果和检查规则中实际可得的项。
6. **检查结果**：每个已配置检查的状态、命令、耗时和诊断摘要。
7. **限制说明**：固定文本必须出现，大意为缺少测试证据不等于代码一定有错，检查未发现问题也不等于代码安全。没有发现时，还要列出实际执行过的检查，并写明这不是“没有缺陷”。

不完整的审核不得使用表示“干净通过”的标题或摘要。

## JSON 顶层

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| schema_version | string | `"1.0"` |
| review_status | string | 三个整次状态之一 |
| policy | object | `mode`、`blocked`、`reasons` |
| metadata | object | 工具版本、配置版本、仓库根、基线、目标、提交标识、变更名、起止时间、限制 |
| summary | object | `needs_human_review`、覆盖计数、`highest_risks`、`reliable_checks`、`disclaimer` |
| changed_files | array | 变更类型、路径、行范围、是否已提交 |
| requirements | array | 标识、语义、证据状态、来源位置 |
| tasks | array | 标识、是否完成、支撑级别 |
| checks | array | 见 CheckResult |
| findings | array | 见 Finding |
| conflicts | array | 互相矛盾的 finding_id |
| artifacts | object | OpenSpec 工件哪些找到、哪些缺失 |

字段没有值时使用 `null` 或空数组，不省略必填键，以免调用方把缺失误认为通过。

## 证据与发现

- `evidence.status` 只允许 `direct`、`inferred`、`insufficient`。
- `findings[].evidence_status` 只允许 `confirmed`、`hypothesis`、`insufficient`。
- 模型产生的发现在没有确定性证据支持时必须是 `hypothesis`。
- `location` 未知时为 `null`，不得填 `0` 或假行号。
- `summary.highest_risks` 的顺序与 Markdown 的风险顺序相同。
- `summary.reliable_checks` 只收录状态为 `PASS` 或已确认 `FAIL` 的检查。`SKIPPED`、`ERROR`、`TIMEOUT` 不列入“不必反复人工确认”。

## 禁止出现的内容

报告正文不包含环境密钥、访问令牌、模型密钥或完整的无关源码。只有 `report.include_source_snippets` 显式开启时才允许短片段，并且片段也要先经过密钥遮盖。遮盖发生时记录“已遮盖”的次数和位置类别，不记录原文。

## 落盘

默认文件名：

- `.specguard/reports/<change>-<target-sha>.md`
- `.specguard/reports/<change>-<target-sha>.json`

没有变更名时使用 `no-change`。写入前重新检查路径。目标已存在时生成不覆盖源码的新文件名，并在元数据中记录最终路径。
