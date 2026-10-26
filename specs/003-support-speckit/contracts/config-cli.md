# Contract: 配置与 CLI

## 新配置

```yaml
version: 1
artifacts:
  provider: speckit
  root: specs
  subject: 003-support-speckit
  include_context: true
git:
  base: main
  target: HEAD
```

`provider` 接受 `openspec`、`speckit` 或 `auto`。`auto` 只有在恰好识别出一种提供方时成功。

## 旧配置兼容

仅含下列配置时，行为保持为 OpenSpec：

```yaml
version: 1
openspec:
  root: openspec
  change: add-order
git:
  base: main
```

同时提供 `artifacts` 和 `openspec` 时：
- 若 `artifacts.provider` 不是 `openspec`，配置失败。
- 若两处 root 或 subject/change 不一致，配置失败。
- 若一致，允许加载并给出弃用提示。

## CLI

新增：

```text
specguard review --subject <id-or-directory>
```

保留：

```text
specguard review --change <openspec-change>
```

规则：
- `--subject` 可用于任一提供方。
- `--change` 仅用于 OpenSpec。
- 两者同时出现且值或提供方语义冲突时退出 `4`。
- CLI 显式值覆盖配置和 Spec Kit 状态文件。
- `help` 和 `version` 不发现或解析工件。

## 错误时序

以下错误必须在构建、测试和辅助审查前返回退出码 `4`：
- 未识别 provider
- 自动检测歧义
- 非法或越界功能目录
- 无效 `.specify/feature.json`
- 冲突的新旧配置
- 重复稳定 ID
