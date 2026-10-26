# Data Model: 从零开始的 OpenSpec 质量门

本功能扩展 v0.2 的 `ArtifactSubject`、`Requirement` 和报告元数据。未列出的字段保持原约束。

## SubjectKind

`current | change | feature`

- OpenSpec 当前规范使用 `current`。
- OpenSpec 进行中的变更使用 `change`。
- Spec Kit 功能使用 `feature`。

## ArtifactProviderConfig 扩展

- `subject_kind`: `current | change | null`。Spec Kit 必须为空。
- `subject`: 仍是变更名或 Spec Kit 功能。`subject_kind: current` 时必须为空。
- 旧配置只有 `openspec.change` 时映射为 `subject_kind: change` 加该变更名。没有变更名时 `subject_kind` 留空，交给发现规则。

## ArtifactSubject 扩展

- `subject_kind`: 见上。
- `subject_id`: 当前规范固定为 `current`；变更仍为变更名。
- `directory`: 当前规范为 `openspec/specs` 的绝对路径；变更仍为对应变更目录。
- `selection_source`: 沿用 `cli | config | feature_state | legacy_config`。只有当前规范、因发现而选中时使用 `legacy_config`，表示沿用 OpenSpec 的唯一对象规则，不是配置里写了变更名。

## BaselineRequirement

复用 `Requirement`，并增加可选字段：

- `capability`: `openspec/specs/<能力>/` 的能力目录名。变更需求为空。
- `identifier`: `<capability>:<slug>`。slug 由需求标题生成，同一能力内重复则在检查前失败。
- `title`: `### Requirement:` 后的原文。
- `body`: 到下一条需求标题之前的正文。空正文失败。
- `change_semantics`: 当前规范必须为 `null`。
- `source_file`、`source_line`: 仓库相对路径和真实标题行。
- `scenarios`: 该需求正文中的 `#### Scenario:`。

关系：一个 `current` 对象包含多个能力，每个能力包含多条需求。一次审核不混入变更需求。

## 任务可用性

`ArtifactBundle` 增加 `tasks_available`：

- 变更对象：发现 `tasks.md` 时为 `true`，即使清单为空。
- 当前规范：为 `false`。
- 没有可审核需求时，需求审核不可用，但该标志仍按对象种类设置。

## 校验

- 当前规范文件必须位于配置根目录内，解析后的真实路径不得离开仓库。
- 无法按 UTF-8 读取、标题重复或正文为空：检查前失败。
- 文件只含增量标题、没有普通需求：检查前失败，并说明应使用变更审核。
- 没有任何 `spec.md`：不构成当前规范。若同时也没有变更，需求审核不可用。

## 报告视图

- `subject_kind` 与 `tasks_available` 同时出现在元数据和工件摘要中。
- 当前规范的找到工件是各能力的 `spec.md`；不把 `proposal.md`、`design.md` 或变更 `tasks.md` 列为缺失。
- 详见 [contracts/report.md](contracts/report.md)。
