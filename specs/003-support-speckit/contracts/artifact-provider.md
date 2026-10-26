# Contract: Artifact Provider

## Provider interface

工件提供方必须实现以下只读行为：

```text
discover(repository, config) -> candidates
select(repository, config, cli_subject) -> ArtifactSubject
validate(subject) -> validation result
load(subject, options) -> ArtifactBundle
```

约束：
- `select` 和 `validate` 失败必须发生在确定性检查与网络调用之前。
- provider 不得写入规格、状态文件、Git 索引或历史。
- `load` 必须返回仓库相对来源路径和真实行号。
- provider 的声明性文档不得直接成为代码实现证据。

## OpenSpec provider

- 默认根：`openspec/`
- 对象：`changes/<change>/`
- 选择：保持现有显式 change 和多活动变更规则
- 需求：`ADDED/MODIFIED/REMOVED Requirements`
- 任务：`tasks.md` 勾选项
- 兼容：现有配置和结果不变

## Spec Kit provider

- 项目标记：`.specify/`
- 默认功能根：`specs/`
- 核心文件：`spec.md`、`plan.md`、`tasks.md`
- 可选上下文：`research.md`、`data-model.md`、`contracts/**`、`quickstart.md`、`checklists/**`

选择优先级：
1. CLI 显式 subject
2. 配置 `artifacts.subject`
3. `.specify/feature.json` 的 `feature_directory`
4. 若仍无法唯一确定则失败

安全规则：
- 状态文件仅只读解析。
- 功能目录解析后必须位于仓库中。
- 拒绝不存在目录、符号链接逃逸和缺少 `spec.md`。
- 不使用 Git 分支名作隐式选择。

解析规则：
- `FR-\d+` 为需求稳定 ID。
- `T\d+` 为任务稳定 ID。
- `[P]` 和 `[USn]` 是任务元数据，不属于任务正文。
- 重复 ID 是校验错误。
- 未替换的关键模板占位符形成错误或明确限制。
