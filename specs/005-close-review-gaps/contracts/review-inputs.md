# Contract: 证据范围与历史对照输入

配置结构版本仍是 `1`。旧配置不写新字段时行为与 v0.3 相同。

## 证据范围

配置：

```yaml
git:
  base: main
  target: HEAD
  evidence_scope: range
```

`evidence_scope` 只接受 `range` 或 `target_tree`，默认 `range`。

命令：

```text
specguard review --config specguard.yaml --evidence-scope target-tree
```

命令值覆盖配置。`target-tree` 对应模型中的 `target_tree`。

拒绝规则：

- 所选对象不是 OpenSpec 当前规范时，`target_tree` 在任何构建、测试或辅助审查之前失败。
- 标准错误包含“完整内容证据范围只适用于当前规范”。
- 退出码为 `4`，不写报告，不修改需求工件或版本历史。
- `--baseline` 与 `--change` 的既有冲突规则不变，先于证据范围检查失败。

`range` 不读取差异之外的文件。`target_tree` 只读取目标版本树中的文件；只有同时传入 `--include-worktree` 时，未提交文件才加入该范围。

## 历史对照记录

路径是已配置报告目录下的 `calibration.json`。解析后的路径必须仍在该报告目录内。系统不创建、不修改这份记录。

```json
{
  "complete": true,
  "reviews": [
    {
      "subject_id": "add-order",
      "finding_ids": ["F001"],
      "verdicts": [
        {"finding_id": "F001", "verdict": "true_issue"}
      ],
      "misses": [],
      "no_misses": true
    }
  ]
}
```

`verdict` 只接受 `true_issue` 与 `false_positive`。

| 输入 | 报告中的对照状态 |
| --- | --- |
| 文件不存在 | `incomplete`，说明历史对照未完成 |
| 不是可读取的记录、结论种类无法识别，或同一发现有矛盾结论 | `incomplete`，说明记录不可用；其他检查保留 |
| `complete` 为真，但没有任何一次完整历史审核 | `incomplete`，且 `rejected_complete_mark` 为真 |
| 至少一次完整历史审核，且 `complete` 为真 | `complete`，并给出数量 |
| 记录含疑似密钥 | 状态按其余字段计算；报告不写出密钥原文 |

完整历史审核的判定见 [data-model.md](../data-model.md)。对照状态不改变默认建议策略，也不单独产生退出码 `2`。
