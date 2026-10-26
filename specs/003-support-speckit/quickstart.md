# Quickstart: 验证 Spec Kit 工件支持

## Prerequisites

- Python 3.11+
- 已安装项目开发依赖
- 一个临时 Git 仓库，包含 `.specify/` 与 `specs/001-sample/`
- 功能目录至少包含 `spec.md`

## Scenario 1: 显式审核 Spec Kit 功能

创建配置，设置：

```yaml
version: 1
artifacts:
  provider: speckit
  root: specs
  subject: 001-sample
git:
  base: HEAD~1
  target: HEAD
review:
  mode: static
  policy: advisory
```

运行：

```bash
specguard review --config specguard.yaml
```

预期：
- 报告记录 `speckit`、`001-sample` 和 `config` 选择来源。
- `FR-*` 与 `T*` 保留原始 ID 和来源行。
- Spec Kit 需求的增量语义为空。
- 未勾选任务不产生“已完成但无支撑”缺口。

## Scenario 2: 使用 Spec Kit 活动功能状态

移除配置中的 `subject`，写入：

```json
{"feature_directory":"specs/001-sample"}
```

到 `.specify/feature.json`，再次运行审核。

预期：
- 选择来源为 `feature_state`。
- 状态文件内容未被修改。
- 报告对象与显式选择场景一致。

## Scenario 3: 验证歧义和非法路径先失败

分别测试：
- `provider: auto` 且仓库同时含 OpenSpec 与 Spec Kit。
- `feature_directory` 指向仓库外。
- `feature_directory` 指向不含 `spec.md` 的目录。

预期：
- 命令退出 `4`。
- 不执行构建、测试或辅助审查。
- 不创建报告，也不改写任何工件。

## Scenario 4: OpenSpec 回归

使用现有 OpenSpec 夹具和旧版配置运行测试：

```bash
pytest tests/unit/test_openspec_parser.py tests/integration/test_us2_requirements.py
```

预期：
- 旧配置无需增加 `artifacts`。
- OpenSpec 的选择、增量语义和报告结论保持不变。

## Full validation

```bash
pytest
```

验收重点：
- 两个 provider 的契约测试均通过。
- Markdown 与 JSON 的工件元数据一致。
- 审核前后规格文件、状态文件、Git 索引和历史不变。
