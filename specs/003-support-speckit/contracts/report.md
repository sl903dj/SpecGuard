# Contract: Report 1.1

结构化报告的 `schema_version` 更新为 `1.1`。

## 新增元数据

```json
{
  "schema_version": "1.1",
  "metadata": {
    "artifact_provider": "speckit",
    "subject_id": "003-support-speckit",
    "selection_source": "feature_state",
    "change": "003-support-speckit"
  },
  "artifacts": {
    "provider": "speckit",
    "subject_id": "003-support-speckit",
    "selection_source": "feature_state",
    "found": ["spec.md", "plan.md", "tasks.md"],
    "missing": [],
    "context_documents": [
      {"kind": "plan", "path": "specs/003-support-speckit/plan.md"}
    ],
    "selected_change": "003-support-speckit"
  }
}
```

## 需求与任务

Spec Kit 需求：
- `identifier` 保留 `FR-*`
- `change_semantics` 为 `null`
- 可含 `user_story_id` 和 `priority`

Spec Kit 任务：
- `identifier` 保留 `T*`
- 可含 `parallel` 和 `user_story_id`

## 兼容字段

以下字段在 1.1 中保留但弃用：
- `metadata.change`
- `artifacts.selected_change`
- `artifacts.main_specs`
- `artifacts.main_requirements`

OpenSpec 报告继续按原语义填充。新消费者使用 `subject_id` 和 `artifact_provider`。

## Markdown

摘要必须显示：
- 工件提供方
- 审核对象
- 选择来源
- 找到和缺失的工件

Markdown 与 JSON 的需求数量、任务缺口、提供方和对象必须一致。
