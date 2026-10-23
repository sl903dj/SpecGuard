# Contract: Spec Kit 需求来源

本契约是 [001 的命令契约](../../001-specguard-quality-gate/contracts/cli.md) 和 [配置契约](../../001-specguard-quality-gate/contracts/config.md) 的增量。未提到的命令、退出码和只读边界保持原样。

## 配置

`requirements.source` 接受 `auto`、`openspec`、`speckit`，默认 `auto`。

`speckit.root` 默认 `specs`。`speckit.feature` 可空。非空时必须是功能目录名。

`openspec` 现有字段保持不变。

## 命令

`specguard review` 增加 `--feature NAME`。它只选择 Spec Kit 功能，并覆盖 `speckit.feature`。

`--change` 仍只选择 OpenSpec 变更。来源解析为 Spec Kit 时再传 `--change`，退出 `4`。来源解析为 OpenSpec 时再传 `--feature`，退出 `4`。

## 选择

| 仓库情况 | 未额外指定 | 指定功能或来源 |
| --- | --- | --- |
| 只有 OpenSpec | 沿用现有 OpenSpec 选择 | `--change` 或配置中的变更名 |
| 只有一个 Spec Kit 功能 | 选中该功能 | `--feature` 必须匹配，否则退出 `4` |
| 多个 Spec Kit 功能 | 退出 `4`，列出目录名；`feature.json` 只出现在提示里 | `--feature` 或 `speckit.feature` 完全匹配其中一个目录名 |
| 两种来源都有候选 | 退出 `4`，列出 `openspec` 和 `speckit` | `requirements.source` 指明一种之后，再按该来源的规则选择 |

停止发生在构建、测试和模型请求之前，并且不创建报告文件。

## 解析

- 规格文件是所选目录的 `spec.md`。功能需求标识使用 `FR-` 加数字。用户故事和验收场景进入报告，但不因标题相似而成为直接证据。
- 任务文件是所选目录的 `tasks.md`。勾选语法只认 `- [ ]`、`- [x]`、`- [X]`。
- 缺少 `tasks.md` 时报告任务工件缺失。缺少可核验需求时，需求符合性不可用。

## 非 Java

项目布局不是受支持的 Java 构建时，不发明构建命令。报告限制说明写明代码检查不支持。整次结果不得是代码风险或测试已经通过。

## 只读

允许的写入仍只有报告目录。不修改 `specs/`、`.specify/`、OpenSpec 目录和 Git 历史。不执行 Spec Kit 命令。
