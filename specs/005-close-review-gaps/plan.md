# Implementation Plan: 补齐质量门的证据与对照能力

**Branch**: `005-close-review-gaps` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-close-review-gaps/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

SpecGuard v0.4 仍审核一份 OpenSpec 变更、一份当前规范或一个 Spec Kit 功能。它补上三件现有报告回答不了的事：需求主证据与验收场景分开、进行中的变更对照已接受的当前规范、历史误报和漏报是否已经对照。同时扩展三类已有能力：九类代码风险每次都给出处置、当前规范可以显式改用目标版本的完整内容作为证据、多模块变更说明仓库级命令没有按模块分别执行。

默认证据范围、默认建议策略和三种审核对象的选择规则不变。对照完成不打开阻断，辅助审查也不能把场景改成已有测试支撑。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Pydantic v2、Typer、PyYAML；继续使用标准库 `pathlib`、`re` 与 `json`，不增加运行时依赖

**Storage**: 无数据库。只读需求工件、版本库和报告目录中的 `calibration.json`。报告仍只写入已配置的报告目录

**Testing**: pytest。先写证据、场景、对照、风险类别、证据范围和模块覆盖的失败测试，再改实现

**Target Platform**: Linux 本地命令行与内网持续集成

**Project Type**: 只读 Python 命令行质量门

**Performance Goals**: 不含构建、测试和模型调用时，1000 条需求、2000 个证据文件和九类风险处置在 5 秒内完成

**Constraints**: 文件名重叠不得写成已实现；场景通过不得回写主证据；当前规范需求不得并入变更清单；看不出的文字差异不得编造成冲突；完整内容证据范围误用时在检查前失败；对照记录只读，密钥不得进报告；没有真实行号不得编造；未执行的模块检查不得标为通过；不修改业务源文件、需求工件或版本历史

**Scale/Scope**: v0.4 一次审核仍只选择一个对象。不扩展到 Java 服务端以外，不新增网页、拉取请求发布或自动合并

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 研究前

| 门禁 | 结果 | 依据 |
| --- | --- | --- |
| I. 质量门而非编程助手 | 通过 | 只读取现有工件并生成报告，不生成或修改业务代码 |
| II. 结论必须有证据 | 通过 | 主证据、场景支撑和未声明冲突都要求可定位来源；看不出时保持人工审核 |
| III. 检查状态诚实 | 通过 | 对照缺失、场景缺失、风险上下文不足和未分别执行的模块都不写成通过 |
| IV. 辅助审查只是假设 | 通过 | 模型输出不能把场景改成已支撑，也不能单独阻断 |
| V. 默认只读且留在内部 | 通过 | 对照记录只从报告目录读取；不新增外部服务；密钥沿用遮盖 |
| v0.1 版本边界 | 通过 | 本功能是 v0.4，不改写 v0.1 只审核 OpenSpec 变更的边界，审核对象仍是 Java 服务端 |
| 多对象不得擅自挑选 | 通过 | 当前规范和 Spec Kit 审核不另选一份变更做对照 |
| 先测试后实现 | 通过 | 六条路径先有失败测试 |
| 简单设计优先 | 通过 | 扩展现有流水线、报告模型和 OpenSpec 解析，不新建服务 |
| 阻断门禁须先有历史对照 | 通过 | 默认保持建议。对照完成不改变策略。已有的显式严格模式仍只接受已证实的确定性失败，并写明对照是否完成 |

研究前没有未解释的宪章偏离。

### 设计后

| 复核项 | 结果 |
| --- | --- |
| 主证据仍只有直接、推断、不足三种，场景结果另存 | 通过 |
| 未声明冲突要求同能力、同标题和明确对立用语，双方都有来源 | 通过 |
| 当前规范需求不进入变更需求列表 | 通过 |
| `calibration.json` 只读，虚假完成标记不打开阻断 | 通过 |
| `target_tree` 只读目标版本树，且误用在检查前失败 | 通过 |
| 九类风险没有行号时记为缺少上下文 | 通过 |
| 模块覆盖不编造命令，跳过状态不是通过 | 通过 |
| 报告 schema 升到 1.3，并保留 1.2 字段 | 通过 |
| 业务源文件、需求工件和版本历史保持只读 | 通过 |

设计后仍无宪章偏离。

## Project Structure

### Documentation (this feature)

```text
specs/005-close-review-gaps/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── report.md
│   └── review-inputs.md
└── tasks.md             # 后续由 /speckit-tasks 生成
```

### Source Code (repository root)

```text
src/specguard/
├── models/entities.py       # 场景正文、对照、风险处置、模块覆盖、schema 1.3
├── config/models.py         # git.evidence_scope，默认 range
├── cli/main.py              # --evidence-scope，误用时退出 4
├── git/diff.py              # 目标版本树的证据文件，不伪装成差异
├── openspec/parser.py       # 场景正文；变更需求保留能力名
├── artifacts/speckit.py     # Spec Kit 场景正文
├── review/
│   ├── traceability.py      # 三种主证据的固定说明
│   ├── scenarios.py         # 场景支撑、缺口和不可用
│   ├── consistency.py       # 未声明冲突与人工审核
│   ├── calibration.py       # 只读对照记录
│   ├── risk.py              # 九类处置
│   └── policy.py            # 对照状态不改变阻断规则
├── project/detect.py        # 变更文件到构建模块
├── pipeline.py              # 按范围取证据，组装新报告段落
└── report/
    ├── markdown.py
    └── json_report.py

tests/
├── unit/
│   ├── test_evidence_scope.py
│   ├── test_scenario_assessment.py
│   ├── test_consistency.py
│   ├── test_calibration.py
│   ├── test_risk_classes.py
│   └── test_module_coverage.py
└── integration/
    └── test_review_gaps.py
```

**Structure Decision**: 继续使用 v0.3 的单一审核流水线。当前规范对照是变更审核的只读上下文，不是新的提供方。证据范围只改变追溯和场景覆盖的可读文件，不改变风险检查所使用的差异。

## Complexity Tracking

无。新的报告段落都挂在现有 `ReviewReport` 上。完整内容证据范围和对照记录没有引入新的服务、存储或第二套审核命令。

## Delivery Sequence

1. 先写失败测试，覆盖 [quickstart.md](quickstart.md) 的六条场景和现有对象回归。
2. 扩展场景正文、证据范围和报告模型，并把结构化报告升到 1.3。
3. 实现三种主证据和场景评估。辅助审查保持为假设。
4. 仅为 OpenSpec 变更加载当前规范对照，输出冲突或人工审核。
5. 读取报告目录中的对照记录，拒绝虚假完成标记，且不改变默认策略。
6. 为九类风险补上处置，并为多模块仓库级命令补上非通过的覆盖说明。
7. 将产品版本更新为 v0.4，补充使用说明，并跑通现有 OpenSpec 与 Spec Kit 回归。
