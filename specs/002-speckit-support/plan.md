# Implementation Plan: SpecGuard 支持 Spec Kit 需求来源

**Branch**: `002-speckit-support` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-speckit-support/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

SpecGuard 在现有只读质量门上增加第二种需求来源。Java 仓库如果用 Spec Kit 的 `specs/<编号-名称>/` 存放规格和任务，审核可以解析这些文件，并沿用已有的证据级别、任务缺口和报告。OpenSpec 仓库保持原行为。两种来源或多个功能同时存在时，必须由工程师指定，不能自动挑选。

技术路径仍是现有的 Python 3.11 命令行工具。新增一个只读的 Spec Kit 发现与解析模块，在进入确定性检查之前选出需求来源。不执行 Spec Kit 命令，不修改规格或任务，不扩大语言范围。

**实现被宪法门禁挡住。** 宪章写明 v0.1 只审核用 OpenSpec 管理需求的 Java 变更。本计划不把这句话解释成已经包含 Spec Kit，也不提供豁免。交付的第一步是修订宪章；修订完成前不得写解析器或改审核流程。

## Technical Context

**Language/Version**: Python 3.11 或更高版本

**Primary Dependencies**: 现有 Typer、Pydantic v2、pytest。不新增 Spec Kit 运行时依赖，也不调用 `specify`。

**Storage**: 无数据库。功能目录和规格只读，报告仍写入配置的报告目录。

**Testing**: pytest。先写失败测试，再用夹具覆盖单个功能、多个功能、OpenSpec 回归，以及非 Java 的 Spec Kit 仓库。

**Target Platform**: 工程师的 Linux 本地环境，以及调用同一命令的内网持续集成作业。被审核仓库自己安装 SpecGuard 命令，不把 SpecGuard 源码克隆进去。

**Project Type**: 只读命令行工具的增量。审核对象仍是 Java / Spring Boot 仓库；需求来源在宪章修订后可以是 OpenSpec 或 Spec Kit。

**Performance Goals**: 不含构建和测试时，规格与任务解析沿用现有 30 秒目标。Spec Kit 解析不增加网络请求。

**Constraints**: 不修改被审核仓库的源文件、规格、任务和 Git 历史。不执行 Spec Kit 命令。多个功能或两种来源都未指定时，在检查前退出。非 Java 项目必须写明代码检查不支持。模型假设和严格策略的默认值不变。

**Scale/Scope**: 一次审核仍只处理一个仓库中的一个选定功能或一个选定 OpenSpec 变更。不提供网页，不合并代码。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 研究前

| 门禁 | 结果 | 依据 |
| --- | --- | --- |
| I. 只做质量门 | 通过 | 只增加需求读取和报告，没有代码生成、任务勾选或合并 |
| II. 结论必须有证据 | 通过 | 直接证据仍要求文件内容含需求标识 |
| III. 检查状态诚实 | 通过 | 非 Java 和缺失规格都不得写成通过 |
| IV. 辅助审查只是假设 | 通过 | 本功能不改变模型假设和默认建议模式 |
| V. 默认只读且留在内部 | 通过 | Spec Kit 文件只读；被审核仓库的原则文本不外发 |
| 范围限于 Java、OpenSpec、Git | **未通过** | 宪章写明需求必须由 OpenSpec 管理。Spec Kit 是第二种需求来源，与该句冲突 |
| 先有测试，确定性检查先于模型 | 通过 | 设计要求先写失败测试；不把辅助审查当成前提 |
| 复杂设计必须说明理由 | 通过 | 见 research.md。不引入第二套报告或数据库 |

研究前的范围门禁未通过。没有豁免。Phase 0 和 Phase 1 只记录修订宪章之后要实现的设计，不授权现在改产品代码。

### 设计后

| 复核项 | 结果 |
| --- | --- |
| 报告仍强制证据状态、免责声明和不完整状态 | 通过 |
| OpenSpec 路径保持为现有行为 | 通过 |
| 多个功能或多个来源在检查前停止 | 通过 |
| 非 Java 仓库明确写不支持，不运行 Maven 或 Gradle 猜测 | 通过 |
| 范围句仍与宪章冲突 | **未通过** |

设计后范围门禁仍然未通过。实现必须等到宪章把 Spec Kit 写成与 OpenSpec 并列的需求来源，并保持只审核 Java 服务端变更。该修订按宪章治理升次版本。本计划不修改 `.specify/memory/constitution.md`。

建议替换的范围句是：系统只审核用版本库管理代码的 Java 服务端变更；需求来源是一个 OpenSpec 变更或一个 Spec Kit 功能目录；两者同时存在或多个候选都未选择时必须停止并列出候选；找不到所选来源或项目不是 Java 时必须说明不支持，不得假装已经覆盖。

## Project Structure

### Documentation (this feature)

```text
specs/002-speckit-support/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── speckit-source.md
└── tasks.md              # 由 /speckit-tasks 生成，本命令不创建
```

### Source Code (repository root)

```text
src/specguard/
├── speckit/              # 新增：只读发现与解析
├── openspec/             # 保持现有 OpenSpec 行为
├── config/               # 增加需求来源和功能名
├── cli/                  # 增加 --feature
└── pipeline.py           # 在检查前选择一个来源

tests/
├── unit/
├── integration/
└── fixtures/
    ├── speckit_single/
    ├── speckit_two/
    └── speckit_not_java/
```

**Structure Decision**: 继续使用现有单一 Python 包。Spec Kit 解析与 OpenSpec 解析并列，汇合到已经存在的需求、任务和报告模型。不新增网页，也不把 Spec Kit 命令嵌进审核流程。

## Complexity Tracking

无豁免。范围门禁未通过，不能用本表把 OpenSpec 限制解释掉。更简单的做法是继续只读 OpenSpec，但那样没有 Spec Kit 审核。正确的下一步是修订宪章，而不是在实现里忽略范围句。

## Delivery Sequence

1. 修订宪章的范围句，使 Spec Kit 功能目录成为允许的需求来源，并保持 Java、只读、证据和默认建议模式。本步骤完成前停止，不实现后续步骤。
2. 为来源选择、单个功能、多个功能、OpenSpec 回归和非 Java 限制先写失败测试。
3. 实现 Spec Kit 目录发现、规格与任务解析，以及 `--feature` 和配置中的来源字段。
4. 在检查开始前接入来源选择。OpenSpec 只有一个变更时的现有路径保持不变。
5. 按 [quickstart.md](quickstart.md) 验证报告、只读边界和拒绝自动挑选。
6. 在 `docs/usage.md` 和 `docs/config-templates.md` 写明如何指定 Spec Kit 功能。模板仍保持静态建议模式。
