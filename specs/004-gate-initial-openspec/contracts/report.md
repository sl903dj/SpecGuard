# Contract: 报告 schema 1.2

`schema_version` 为 `1.2`。1.1 的 `artifact_provider`、`subject_id`、`selection_source`、上下文清单，以及弃用的 `metadata.change` 和 `artifacts.selected_change` 继续存在。

## 新增字段

元数据和 `artifacts` 都包含：

- `subject_kind`: `current`、`change` 或 `feature`。
- `tasks_available`: 布尔值。

当前规范示例：

```json
{
  "schema_version": "1.2",
  "metadata": {
    "change": null,
    "artifact_provider": "openspec",
    "subject_id": "current",
    "subject_kind": "current",
    "tasks_available": false
  },
  "artifacts": {
    "subject_kind": "current",
    "tasks_available": false,
    "selected_change": null,
    "found": ["specs/order/spec.md"]
  }
}
```

需求保留 `capability`。当前规范需求的 `change_semantics` 为 `null`。

## 呈现

- Markdown 在工件来源中写明“当前规范”或“进行中的变更”。
- `tasks_available` 为 `false` 时写“任务完整性不可用”，不以零缺口表示任务通过。
- 没有可审核需求时写“基于需求的审核不可用”。
- Markdown 与 JSON 的对象种类、需求数和缺失工件一致。
- 缺失项不包含当前规范本来就没有的 `proposal.md` 或变更 `tasks.md`。
