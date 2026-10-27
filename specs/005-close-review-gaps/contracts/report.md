# Contract: 报告 schema 1.3

`schema_version` 为 `1.3`。1.2 的 `subject_kind`、`tasks_available`、`artifact_provider`、`subject_id`、`selection_source`，以及弃用的 `metadata.change` 和 `artifacts.selected_change` 继续存在，含义不变。

## 新增字段

```json
{
  "schema_version": "1.3",
  "metadata": {
    "evidence_scope": "range",
    "calibration": {
      "status": "incomplete",
      "completed_review_count": 0,
      "rejected_complete_mark": false,
      "notes": ["历史对照未完成"]
    },
    "module_coverage": {
      "changed_modules": ["."],
      "execution": "repository",
      "not_separately_covered": []
    },
    "risk_dispositions": [
      {"risk_class": "boundary", "disposition": "missing_context"}
    ]
  },
  "scenario_assessments": [
    {
      "requirement_id": "order:create-order",
      "scenario_name": "拒绝空数量",
      "status": "gap",
      "test_file": null,
      "test_line": null,
      "note": "测试没有检查场景写出的预期结果"
    }
  ],
  "consistency_items": []
}
```

`evidence_scope` 只取 `range` 或 `target_tree`。九个 `risk_class` 每次都出现且不重复。`scenario_assessments.status` 只取 `supported`、`gap`、`unavailable`。`consistency_items.status` 只取 `conflict`、`human_review`。

## 呈现

- Markdown 摘要依次写出最弱需求证据、未声明冲突数量、历史对照状态，以及应先看的最高风险。
- 主证据说明使用数据模型中的三句固定文字。文件名重叠不得写成已经实现。
- `supported` 给出测试路径和行号。`gap` 与 `unavailable` 不因测试命令通过而写成已满足。
- 没有当前规范时写“规范对照不可用”。当前规范或 Spec Kit 审核写“未做 OpenSpec 当前规范对照”。已声明的修改或删除不出现在冲突列表。
- 对照未完成时写“历史对照未完成”。完成标记被拒绝时同时写明标记已拒绝。完成时写出完整历史审核的数量。两种状态都不把默认结果写成阻止合并。
- 风险段落列出九类。没有发现时写明这些类别已检查，并保留“未发现问题不等于代码安全”。
- 多个模块未被分别覆盖时，Markdown 点名这些模块。对应检查状态不是通过，命令为空。
- Markdown 与 JSON 的证据计数、场景状态、冲突、对照状态和风险处置一致。
- 报告不包含对照记录或源文件中的密钥原文。遮盖只记录类别和次数。

## 不改变的结论

- 任务完整性在当前规范上仍为不可用。
- 辅助审查发现的证据状态仍不是已证实，且不单独造成阻断。
- 审核完成、未完成和策略阻断的退出码含义不变。
