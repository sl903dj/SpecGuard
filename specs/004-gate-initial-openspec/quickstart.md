# Quickstart: 从零开始的 OpenSpec 质量门

验证本功能的四条路径。命令和字段以 [baseline-selection.md](contracts/baseline-selection.md) 与 [report.md](contracts/report.md) 为准。完整测试在实现阶段用 pytest 执行。

## 准备

- Python 3.11+ 和项目测试环境。
- 三个临时 Git 仓库：只有 `openspec/specs/`、只有 `openspec/changes/`、两者都有。
- 版本范围只包含一部分实现文件，并在范围外保留另一个已存在文件。

## 场景 1: 只有当前规范

配置 `subject_kind: current`，或不写对象并省略 `--change`。

预期：

- 审核不要求变更名。
- 报告 `subject_kind` 为 `current`，需求语义为空。
- 范围内有证据的需求给出位置；范围内没有证据的需求为证据不足。
- 范围外文件不被引用为证据。
- 报告写明任务完整性不可用。
- `openspec/` 与 Git 历史不变。

## 场景 2: 只有变更

使用现有单变更和多变更样例，不添加当前规范。

预期：单变更仍可审核并保留增量语义；多个变更且未选择时退出 `4`。既有回归通过。

## 场景 3: 规范和变更并存

不传 `--baseline` 或 `--change` 时退出 `4`，并且没有报告文件。然后分别用 `--baseline` 和 `--change <名称>` 各审核一次。

预期：两次报告的对象种类不同；变更审核不包含当前规范的其他需求，当前规范审核不包含变更增量。

## 场景 4: 冲突与损坏输入

同时传入 `--baseline` 和 `--change`，以及一份正文为空或标题重复的当前规范。

预期：两次都在检查开始前退出 `4`，不写报告，不修改规范。

## 验证记录

2026-10-26 在本机用 `.venv/bin/python -m pytest -q` 跑完整测试，149 项通过。四条场景分别由 `tests/integration/test_baseline_review.py`、`tests/unit/test_baseline_selection.py`、`tests/integration/test_provider_compatibility.py` 和 `tests/unit/test_cli.py` 覆盖。没有发现需要单独记录的环境限制。
