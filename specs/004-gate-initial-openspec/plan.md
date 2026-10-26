# Implementation Plan: 从零开始的 OpenSpec 质量门

**Branch**: `004-gate-initial-openspec` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-gate-initial-openspec/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

SpecGuard v0.3 让 OpenSpec 的当前规范本身成为质量门对象。`openspec/specs/<能力>/spec.md` 中的 `### Requirement:` 作为全部需求进入审核，`change_semantics` 保持为空。证据仍只来自工程师选定的 Git 版本范围；范围外文件不算实现。当前规范默认没有任务清单，报告必须说明任务完整性不可用。

进行中的变更审核保持增量语义。只有变更时，沿用现有单变更自动选择和多变更要求选择的规则。当前规范与变更同时存在且没有显式选择时，在检查前失败。`--baseline` 与 `--change` 冲突时同样失败。Spec Kit 路径不改变。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Pydantic v2、Typer、PyYAML；继续使用标准库 `pathlib` 与 `re`，不增加运行时依赖

**Storage**: 无数据库；只读 `openspec/specs/` 与 `openspec/changes/`，报告仍写入配置的报告目录

**Testing**: pytest；先写当前规范解析、选择歧义、版本范围证据和变更回归的失败测试

**Target Platform**: Linux 本地 CLI 与内网 CI

**Project Type**: 只读 Python 命令行质量门

**Performance Goals**: 不含构建、测试和模型调用时，解析 100 个能力目录、1000 条当前规范需求在 5 秒内完成

**Constraints**: 不扫描版本范围之外的文件；不把主规范需求标成 added、modified 或 removed；不修改规范或 Git；选择冲突在检查和网络调用前失败；Spec Kit 与仅有变更的旧仓库行为保持不变

**Scale/Scope**: v0.3 一次审核只选择当前规范或一份变更，不合并两类需求；不改变 Java 服务端审核范围，也不评估规范文笔

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 研究前

| 门禁 | 结果 | 依据 |
| --- | --- | --- |
| I. 质量门而非编程助手 | 通过 | 只读取当前规范并生成报告，不生成、补全或归档规范 |
| II. 结论必须有证据 | 通过 | 证据限定在选定版本范围；不足不写成通过或确定缺陷 |
| III. 检查状态诚实 | 通过 | 没有任务清单时说明不可用，不把缺口 0 当成任务通过 |
| IV. 辅助审查只是假设 | 通过 | 不新增模型路径，现有假设规则不变 |
| V. 默认只读且留在内部 | 通过 | 规范、索引和历史只读；不新增外部服务 |
| v0.1 版本边界 | 通过 | v0.1 仍只覆盖 OpenSpec 变更；本功能作为 v0.3 增加当前规范对象，不回溯改写 v0.1 |
| 多对象不得擅自挑选 | 通过 | 当前规范与变更并存时失败，而不是猜测 |
| 先测试后实现 | 通过 | 选择、解析和范围证据先有失败测试 |
| 简单设计优先 | 通过 | 扩展现有 OpenSpec 适配器，不新建第二套审核流水线 |

研究前没有未解释的宪章偏离。

### 设计后

| 复核项 | 结果 |
| --- | --- |
| 当前规范需求的 `change_semantics` 为空 | 通过 |
| 版本范围外文件不构成证据 | 通过 |
| 两类对象并存或 `--baseline`/`--change` 冲突时在检查前失败 | 通过 |
| 显式变更审核仍使用 ADDED/MODIFIED/REMOVED | 通过 |
| 仅有变更、没有当前规范时保留原选择规则 | 通过 |
| 报告 schema 升到 1.2，并保留 1.1 字段 | 通过 |
| 规范工件和 Git 保持只读 | 通过 |

设计后仍无宪章偏离。

## Project Structure

### Documentation (this feature)

```text
specs/004-gate-initial-openspec/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── baseline-selection.md
│   └── report.md
└── tasks.md             # 后续由 /speckit-tasks 生成
```

### Source Code (repository root)

```text
src/specguard/
├── artifacts/
│   ├── models.py         # 增加 subject_kind
│   └── openspec.py       # 当前规范发现、选择与加载
├── openspec/parser.py    # 解析主规范需求，拒绝增量语义冒充
├── config/models.py      # subject_kind 与旧配置兼容
├── cli/main.py           # --baseline 与 --change 冲突
├── models/entities.py    # 能力名称、任务可用性、schema 1.2
├── pipeline.py           # 缺任务时不宣称任务通过
└── report/
    ├── markdown.py
    └── json_report.py

tests/
├── fixtures/baseline/    # 只有当前规范、规范与变更并存
├── integration/
│   ├── test_baseline_review.py
│   └── test_provider_compatibility.py
└── unit/
    ├── test_baseline_parser.py
    └── test_baseline_selection.py
```

**Structure Decision**: 继续使用 v0.2 的 OpenSpec 适配器。当前规范是该适配器的第二种对象，不是新的提供方。追溯、风险、测试和策略阶段继续消费 `ArtifactBundle`。

## Complexity Tracking

无。显式对象种类是为了避免把整份规范和一次变更混为同一个需求来源，不增加服务或第二套流水线。

## Delivery Sequence

1. 先写失败测试：主规范解析、空语义、重复标识、只有当前规范、两类对象并存、版本范围外文件、变更回归。
2. 为 OpenSpec 对象增加 `current` 与 `change`，并在配置和 `--baseline` 中表达选择。
3. 加载 `openspec/specs/<能力>/spec.md`，保留能力名称和来源行，不制造增量语义。
4. 缺需求或任务清单时写入明确限制，避免报告把不可用写成通过。
5. 将报告契约升到 1.2，Markdown 与 JSON 都标明对象种类。
6. 将产品版本更新为 v0.3，补充使用说明，并跑通现有 OpenSpec 与 Spec Kit 回归。
