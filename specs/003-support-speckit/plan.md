# Implementation Plan: Spec Kit 工件支持

**Branch**: `003-support-speckit` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-support-speckit/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

SpecGuard 在保留 OpenSpec 行为的同时，增加 GitHub Spec Kit 工件审核能力。系统从 `spec.md` 和 `tasks.md` 提取稳定的 `FR-*`、`T*` 标识及验收信息，并登记计划、研究、数据模型、契约和检查清单作为只读上下文。

实现采用中立 `ArtifactProvider` 边界：OpenSpec 与 Spec Kit 适配器负责各自的发现、选择、校验和解析，输出统一 `ArtifactBundle`；现有追溯、测试有效性、风险、策略和报告流水线继续消费规范化模型。Spec Kit 对象选择遵循显式 CLI/配置、`.specify/feature.json`、歧义失败的顺序，不使用 Git 分支名猜测。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Pydantic v2、Typer、PyYAML；使用标准库 `json`、`pathlib` 和 `re` 解析 Spec Kit 工件，不增加运行时依赖

**Storage**: 无数据库；只读规格文件与 `.specify/feature.json`，报告继续写入配置目录

**Testing**: pytest；提供方契约测试、解析单元测试、配置/CLI 测试、端到端报告和只读回归

**Target Platform**: Linux 本地 CLI 与内网 CI

**Project Type**: 只读 Python 命令行质量门

**Performance Goals**: 不含构建、测试和模型调用时，发现和解析 100 个功能目录、1000 条需求及 5000 条任务在 5 秒内完成

**Constraints**: 旧版 OpenSpec 配置无需修改；选择错误必须在检查前失败；不得修改 Spec Kit 状态或工件；不得将计划文字当实现证据；不新增任意外部校验命令

**Scale/Scope**: 首版支持一个审核命令选择一个 OpenSpec 变更或 Spec Kit 功能；不支持同时合并两种提供方的需求，也不改变 Java 审核范围

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 研究前

| 门禁 | 结果 | 依据 |
| --- | --- | --- |
| I. 质量门而非编程助手 | 通过 | 只读取规格并生成审核报告，不生成业务代码或修改功能工件 |
| II. 结论必须有证据 | 通过 | 计划和上下文文档不直接成为实现证据；保留直接、推断和不足 |
| III. 检查状态诚实 | 通过 | 工件选择和校验错误在检查前失败，不降级为通过 |
| IV. 辅助审查只是假设 | 通过 | 新上下文仍经过遮盖、截断和假设标记 |
| V. 默认只读且留在内部 | 通过 | `.specify/feature.json` 和功能目录只读；不新增外部服务 |
| v0.1 范围 | 通过 | 仍审核 Git 管理的 Java 服务端项目，只扩展需求工件格式 |
| 先测试后实现 | 通过 | 提供方契约和 Spec Kit 夹具先锁定失败行为 |
| 简单设计优先 | 通过 | 一个小型 provider 边界复用现有核心，不复制审核流水线 |

研究前没有未解释的宪章偏离。

### 设计后

| 复核项 | 结果 |
| --- | --- |
| Spec Kit 需求不伪造增量语义 | 通过 |
| 显式/状态文件选择失败发生在检查和网络调用前 | 通过 |
| 上下文文档不提升证据等级 | 通过 |
| 状态文件、规格工件和 Git 保持只读 | 通过 |
| OpenSpec 旧配置及 CLI 语义保留 | 通过 |
| 报告契约变化有 1.1 版本和弃用过渡 | 通过 |

设计后仍无宪章偏离。

## Project Structure

### Documentation (this feature)

```text
specs/003-support-speckit/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── artifact-provider.md
│   ├── config-cli.md
│   └── report.md
└── tasks.md             # 后续由 /speckit-tasks 生成
```

### Source Code (repository root)

```text
src/specguard/
├── artifacts/
│   ├── models.py         # provider、subject、bundle、context
│   ├── provider.py       # 只读 provider 协议与选择协调
│   ├── openspec.py       # 迁入现有 OpenSpec 发现与加载
│   └── speckit.py        # Spec Kit 状态、发现、校验与解析
├── config/models.py      # 新配置与旧 openspec 兼容映射
├── cli/main.py           # --subject 与 --change 兼容规则
├── models/entities.py    # 可空语义及通用工件元数据
├── pipeline.py           # 改为消费 ArtifactBundle
└── report/
    ├── markdown.py
    └── json_report.py

tests/
├── fixtures/
│   ├── single_change/    # 保留 OpenSpec 回归
│   └── speckit/          # 单功能、多功能、非法状态和双提供方
├── integration/
│   ├── test_speckit_review.py
│   └── test_provider_compatibility.py
└── unit/
    ├── test_artifact_provider.py
    ├── test_speckit_discovery.py
    └── test_speckit_parser.py
```

**Structure Decision**: 新建 `artifacts/` 作为唯一格式边界。现有 `openspec/` 逻辑迁入适配器或通过薄包装复用，完成过渡后删除核心流水线对格式目录的直接导入。审核模型和后续分析仍保留在原目录，避免为每种格式复制业务逻辑。

## Complexity Tracking

无。提供方边界是隔离两套已确认不同的格式规则所需的最小抽象，没有新增服务、数据库或第二套审核核心。

## Delivery Sequence

1. 先为 provider 契约、Spec Kit 状态选择、FR/T 解析和旧 OpenSpec 配置写失败测试。
2. 增加中立模型和 provider 协议，包装现有 OpenSpec 行为，确保回归先恢复为绿。
3. 实现 Spec Kit 目录边界校验、`.specify/feature.json` 只读选择和工件解析。
4. 将流水线切换为 `ArtifactBundle`，复用现有追溯、任务、测试和风险审核。
5. 扩展配置与 CLI，处理新旧字段、`--subject`/`--change` 冲突和 auto 歧义。
6. 将报告契约升级到 1.1，增加提供方、对象和选择来源，并保留弃用别名。
7. 把上下文文档接入受限辅助审查，验证遮盖、截断和不可信输入规则。
8. 更新配置模板、使用说明和报告解释，运行完整 OpenSpec 与 Spec Kit 端到端回归。
