# 如何阅读 SpecGuard 报告

SpecGuard 是变更质量门。报告帮助工程师决定先看哪里，不代替接受或拒绝变更。

## 报告 schema 1.2

`metadata.artifact_provider`、`subject_id` 和 `selection_source` 标明工件来源、审核对象和选择来源。`subject_kind` 为 `current`（当前规范）、`change`（进行中的变更）或 `feature`（Spec Kit 功能）。`tasks_available` 为 `false` 时，Markdown 写「任务完整性不可用」，不能把任务缺口 `0` 读成任务已经通过。`artifacts.context_documents` 只列上下文种类与路径，不输出内容。Markdown 的工件来源、需求数量和任务说明应与 JSON 一致。

`metadata.change`、`artifacts.selected_change`、`main_specs` 和 `main_requirements` 是兼容字段。当前规范报告里前两个字段为空。新消费者应使用中立字段。Spec Kit 需求和当前规范需求的 `change_semantics` 为 `null`，不是缺失数据。当前规范不会把 `proposal.md` 或变更 `tasks.md` 列为必须存在的工件。

## 检查状态

每项检查只有一个状态：

- `PASS`：命令已执行且退出码为 0。
- `FAIL`：命令已执行且退出码不是 0。
- `SKIPPED`：检查没有执行，例如工具未安装且该检查不是必需的。
- `ERROR`：检查无法执行，例如必需工具缺失或配置了检查但没有命令。
- `TIMEOUT`：超过时限，进程已被终止。

`SKIPPED`、`ERROR`、`TIMEOUT` 都不是通过。

## 整次状态

- `REVIEW_COMPLETE`：必需检查都有明确结果，且策略没有阻断。报告里仍可以有发现。
- `REVIEW_INCOMPLETE`：有必需检查未完成，或审核期间版本库变了。这不是干净通过。
- `POLICY_BLOCKED`：调用方明确选择了严格策略，且命中了已确认的确定性失败。模型假设不会单独造成这个状态。

## 证据

- `direct`：变更内容里能找到需求标识。
- `inferred`：只有文件名一类的重叠，不能单独证明需求已实现。
- `insufficient`：没有找到证据。

证据不足不是“代码一定有错”。没有发现，或静态检查没有报问题，也不是“代码安全”或“没有缺陷”。

## 退出码

- `0`：审核完成且未阻断。
- `1`：程序内部错误。
- `2`：严格策略阻断。
- `3`：审核不完整。
- `4`：配置、版本库或变更选择无法开始审核。
