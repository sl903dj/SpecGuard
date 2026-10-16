# Implementation Plan: SpecGuard 变更质量守卫

**Branch**: `001-specguard-quality-gate` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-specguard-quality-gate/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

SpecGuard v0.1 是一个本地只读的变更质量门。工程师对一份 OpenSpec 变更运行一次审核，得到 Markdown 和 JSON 报告，用来回答需求符合性、任务完整性、代码风险、测试有效性和审核效率，并为每条结论附上可核查的证据。

技术路径：Python 3.11 命令行工具先读取 Git 差异和 OpenSpec，再执行配置中允许的构建与测试，最后才可选地调用内网模型。模型输出在有确定性证据之前只算假设。默认策略是建议模式，不自动合并，也不在历史变更对照完成前充当阻止合并的门禁。选择和理由见 [research.md](research.md)。

使用者把 `specguard` 安装到本机命令路径，再到被审核的 Java 仓库里运行。不把 SpecGuard 源码克隆进该仓库。这与 Spec Kit 的 `specify` 相同：命令来自安装器，项目里不保留工具源码。v0.1 的安装入口是 Python 控制台脚本，不要求单独交付一个原生二进制。SpecGuard 自己的开发和测试仍使用本仓库的源码检出。

交付顺序固定为：配置与报告模型、只读 Git 与 OpenSpec 解析、确定性检查、证据追溯、报告与退出码、内网辅助审查、严格策略信号。辅助审查不能成为前面各步可用的前提。

## Technical Context

**Language/Version**: Python 3.11 或更高版本

**Primary Dependencies**: Typer（命令）、Pydantic v2（配置与报告模型）、pytest（测试）、本机 Git、受信任的 Maven 或 Gradle 命令。辅助审查使用内网 OpenAI 兼容 HTTP 接口。具体版本在实现时按内网环境锁定。

**Storage**: 无数据库。单次审核的状态留在内存中，报告写入配置的报告目录。

**Testing**: pytest。先写失败测试，再用夹具覆盖版本库、OpenSpec、检查状态和报告契约。

**Target Platform**: 工程师的 Linux 本地环境，以及以后可以调用同一命令的内网持续集成作业。v0.1 不提供网页。使用者安装 `specguard` 命令；被审核仓库只放 `specguard.yaml` 和它自己的源码。

**Project Type**: 只读命令行工具。审核对象是使用 OpenSpec 和 Git 的 Java / Spring Boot 仓库。分发方式对齐 Spec Kit：安装命令，不在目标项目里拉取工具源码。

**Performance Goals**: 不含构建和测试时，一次普通服务变更的仓库与需求解析在 30 秒内完成。构建和测试分别服从配置超时，示例上限为构建 600 秒、测试 900 秒。模型上下文默认不超过 50000 个字符。

**Constraints**: 不修改被审核仓库的源文件、OpenSpec 和 Git 历史。使用者不需要克隆 SpecGuard 源码才能审核。配置无效时在检查前退出。检查状态只能是通过、失败、跳过、错误或超时。未配置内部模型时不访问外部模型。模型假设默认不阻断。

**Scale/Scope**: 一次命令审核一个仓库中的一个选定变更。v0.1 不覆盖 Java 以外的项目，不提供审核平台，也不绑定某个编程助手。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

规格中“宪章仍是未填写模板”的假设已经过时。本计划以宪章 1.0.0 为准。

### 研究前

| 门禁 | 结果 | 依据 |
| --- | --- | --- |
| I. 只做质量门 | 通过 | 计划只有审核命令和报告，没有代码生成、提交或合并 |
| II. 结论必须有证据 | 通过 | 证据分为直接、推断和不足；不足不写成缺陷 |
| III. 检查状态诚实 | 通过 | 五种检查状态和三种整次状态分开，未执行不是通过 |
| IV. 辅助审查只是假设 | 通过 | 模型发现默认不阻断；阻断式门禁不是默认部署 |
| V. 默认只读且留在内部 | 通过 | Git 与 OpenSpec 只读；模型地址必须显式配置且禁止回退 |
| 范围限于 Java、OpenSpec、Git | 通过 | 无法识别的布局要说明限制 |
| 先有测试，确定性检查先于模型 | 通过 | 交付顺序把辅助审查放在检查和报告之后 |
| 复杂设计必须说明理由 | 通过 | 不引入数据库、网页或第二套 Git 实现 |

研究前没有未解释的宪章偏离，可以进入 Phase 0。

### 设计后

Phase 1 的数据模型、命令契约、配置契约和报告契约落实了上述门禁。

| 复核项 | 结果 |
| --- | --- |
| 报告模型强制证据状态、免责声明和不完整状态 | 通过 |
| 退出码 `2` 只在显式严格策略且确定性失败时出现 | 通过 |
| `review.llm_findings_block: true` 被配置契约拒绝 | 通过 |
| 报告路径逃逸在写入前拒绝 | 通过 |
| 构建隔离用于不可信仓库，失败时检查为错误而不是通过 | 通过 |
| 命令允许列表阻止模型生成的任意命令 | 通过 |

设计后仍然没有需要豁免的偏离。

## Project Structure

### Documentation (this feature)

```text
specs/001-specguard-quality-gate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── config.md
│   └── report.md
└── tasks.md              # 由 /speckit-tasks 生成，本命令不创建
```

### Source Code (repository root)

```text
src/specguard/
├── cli/                  # 命令、退出码
├── config/               # 配置加载与允许列表
├── models/               # 报告、发现、检查结果
├── git/                  # 只读版本库适配
├── openspec/             # 只读需求与任务解析
├── project/              # Maven、Gradle 与模块识别
├── checks/               # 超时、状态和可选工具适配
├── review/               # 追溯、风险、测试有效性、策略
├── llm/                  # 可选的内网模型适配
└── report/               # Markdown 与 JSON

tests/
├── unit/
├── integration/
└── fixtures/             # 小型 Git 与 OpenSpec 样例仓库
```

**Structure Decision**: 使用单一 Python 包，而不是网页的前后端结构。每个目录对应设计包中的一个边界：命令、版本库、OpenSpec、项目识别、检查执行、审核、模型和报告。测试分单元、集成和夹具，避免把样例 Java 仓库混进产品源码。

## Complexity Tracking

无。本计划未引入需要豁免的宪章偏离。构建工具可能在受信任仓库中产生构建产物；这一风险由配置说明和不可信仓库的隔离工作区承担，不构成对只读原则的豁免。

## Delivery Sequence

1. 建立包、配置模型和五种检查状态，并先用测试锁住“无效配置不开始审核”。
2. 实现只读 Git 差异和 OpenSpec 解析，包括拒绝含糊变更和非法基线。
3. 实现确定性检查执行器与 Maven / Gradle 识别。静态模式到此必须可以出报告。
4. 实现需求、任务和测试证据的三级追溯，以及 Markdown 与 JSON 报告。
5. 按 [quickstart.md](quickstart.md) 验证静态模式、只读边界和退出码。
6. 再实现内网辅助审查、密钥遮盖和假设标记。
7. 最后实现显式严格策略的退出码。默认配置保持建议模式，不安装合并门禁。
