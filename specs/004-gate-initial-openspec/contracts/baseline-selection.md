# Contract: OpenSpec 当前规范选择

## 对象

| 种类 | 位置 | 需求来源 |
| --- | --- | --- |
| `current` | `openspec/specs/<能力>/spec.md` | 普通 `### Requirement:` |
| `change` | `openspec/changes/<变更名>/` | ADDED、MODIFIED、REMOVED |

一次审核只能有一种需求来源。

## 配置

```yaml
version: 1
artifacts:
  provider: openspec
  subject_kind: current
git:
  base: main
```

审核某个变更时：

```yaml
artifacts:
  provider: openspec
  subject_kind: change
  subject: add-order
```

`subject_kind: current` 再写 `subject` 或 `openspec.change` 时，配置校验失败。只写旧的 `openspec.change` 时，行为与 `subject_kind: change` 相同。

## CLI

```text
specguard review --config specguard.yaml --baseline
specguard review --config specguard.yaml --change add-order
```

`--baseline` 与 `--change` 同时出现时，在检查前退出 `4`。`--baseline` 也不能配合配置里的变更名。

## 未显式选择

1. 只有变更：一个变更则选择它；多个变更则退出 `4`。
2. 只有当前规范：选择 `current`。
3. 两者都有：退出 `4`，提示使用 `--baseline` 或 `--change`。
4. 两者都没有：需求审核不可用，不宣称需求通过。

失败发生在构建、测试、模型调用和报告写入之前。

## 解析拒绝

- 需求标题在同一能力内重复。
- 需求正文为空。
- 文件不是合法 UTF-8，或真实路径离开仓库。
- 当前规范文件只包含增量标题。
