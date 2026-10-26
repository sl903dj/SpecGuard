# Data Model: Spec Kit 工件支持

## ArtifactProviderConfig

选择需求工件来源。

- `provider`: `openspec | speckit | auto`
- `root`: 仓库相对路径；OpenSpec 默认 `openspec`，Spec Kit 默认 `specs`
- `subject`: 可选的审核对象标识或功能目录
- `include_context`: 是否登记设计上下文，默认 `true`

验证规则：
- 路径解析后必须位于仓库内。
- `provider=auto` 且同时发现两类有效工件时失败。
- 与旧 `openspec` 配置同时出现时，不一致的选择必须失败。

## ArtifactSubject

一次需求审核的中立对象。

- `provider`: 工件提供方
- `subject_id`: OpenSpec 变更名或 Spec Kit 功能目录名
- `directory`: 已验证的仓库内绝对路径
- `selection_source`: `cli | config | feature_state | legacy_config`

状态转换：

```text
candidate -> selected -> validated -> loaded
     |          |           |
     +----------+-----------+-> rejected
```

在 `validated` 前不得执行构建、测试或辅助审查。

## ArtifactBundle

提供方输出给审核核心的规范化工件包。

- `subject`: `ArtifactSubject`
- `found`: 已找到的逻辑工件
- `missing`: 缺失的提供方工件
- `requirements`: `Requirement[]`
- `tasks`: `TaskItem[]`
- `context_documents`: `ContextDocument[]`
- `limitations`: 加载限制

OpenSpec 和 Spec Kit 必须遵守同一输出契约，但各自定义必需工件。

## Requirement

在现有字段上扩展：

- `identifier`: 来源中的稳定 ID
- `title`, `body`, `source_file`, `source_line`
- `change_semantics`: `added | modified | removed | null`
- `user_story_id`: Spec Kit 可选 `USn`
- `priority`: Spec Kit 可选 `P1 | P2 | P3 | ...`
- `scenarios`: 验收场景
- `evidence`: 现有三级证据

规则：
- OpenSpec 继续要求增量语义。
- Spec Kit 的增量语义必须为 `null`。
- 同一工件包内需求 ID 必须唯一。

## TaskItem

在现有字段上扩展：

- `identifier`: `T*` 或 OpenSpec 原任务 ID
- `text`, `marked_complete`, `source_file`, `source_line`
- `parallel`: 是否有 `[P]`
- `user_story_id`: 可选 `[USn]`
- `support`, `evidence`: 现有支撑信息

同一工件包内任务 ID 必须唯一。任务勾选本身不构成实现证据。

## ContextDocument

- `kind`: `plan | research | data_model | contract | quickstart | checklist | proposal | design | main_spec`
- `path`: 仓库相对路径
- `title`: 可选标题
- `content`: 受大小上限约束的文本，报告默认不直接输出

上下文可以帮助解释发现，但不得直接把证据状态提升为 `direct`。

## ArtifactReport

在现有报告模型上增加：

- `provider`
- `subject_id`
- `selection_source`
- `context_documents`: 只输出种类与路径

兼容字段：
- `selected_change`: 兼容期保留；OpenSpec 填原值，Spec Kit 可填 `subject_id`
- `main_specs`, `main_requirements`: 仅 OpenSpec 兼容输出，标记弃用

## Metadata

增加：

- `artifact_provider`
- `subject_id`
- `selection_source`

`change` 在兼容期保留。新消费者必须使用 `subject_id`。
