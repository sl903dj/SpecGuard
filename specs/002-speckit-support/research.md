# Research: SpecGuard 支持 Spec Kit 需求来源

本功能没有遗留的 `NEEDS CLARIFICATION`。范围与宪章冲突的处理方式是先修订宪章，而不是把冲突写成设计豁免。

## Decision: Spec Kit 是第二种只读需求来源

- **Decision**: 被审核仓库的 `specs/<编号-名称>/spec.md` 与同目录 `tasks.md` 可以提供需求和任务。编号是目录名开头的十进制数字。没有 `spec.md` 的目录不是候选功能。解析结果进入现有的需求、任务和报告模型。SpecGuard 不运行 `specify`，不读取 `.specify/extensions.yml` 来执行钩子。
- **Rationale**: Spec Kit 的规格和任务已经是工程师用来描述变更的文件。再要求他们维护一份 OpenSpec，质量门就无法覆盖正在使用 Spec Kit 的 Java 仓库。只读解析能复用证据、任务缺口和报告，而不把 SpecGuard 变成另一个 Spec Kit 命令。
- **Alternatives considered**: 继续只认 OpenSpec，完不成这个功能。把 Spec Kit 仓库转换成临时 OpenSpec 目录会写入被审核仓库，违反只读。调用本机 `specify` 会把审核绑到 Spec Kit 的命令实现，并可能触发钩子。

## Decision: 候选多于一个时停止，feature.json 只作为提示

- **Decision**: 零个 Spec Kit 功能且来源被指定为 Spec Kit 时，基于需求的审核不可用。一个功能时选中它。多个功能时，只有配置 `speckit.feature` 或命令 `--feature` 能选中；名称必须完全匹配目录名。`.specify/feature.json` 的 `feature_directory` 如果指向其中一个候选，只写进停止信息，不自动选中。OpenSpec 与 Spec Kit 同时存在时，配置 `requirements.source` 必须是 `openspec` 或 `speckit`；`auto` 只在恰好一种来源有候选时可用。
- **Rationale**: 宪章禁止在多个进行中的变更里擅自挑选。`feature.json` 表示 Spec Kit 工具上次使用的功能，不表示工程师这次要审核的功能。
- **Alternatives considered**: 默认采用 `feature.json` 会在仓库含有多个功能时静默审错对象。把 `--change` 同时用于 Spec Kit 功能名会和 OpenSpec 变更名混在同一个参数里。

## Decision: 证据和任务规则不另起一套

- **Decision**: 功能需求标识出现在变更文件内容中才是直接证据。文件名重叠最多是推断。规格里的用户故事和验收场景随功能需求一起报告；故事标题单独重叠不是直接证据。`tasks.md` 里 `- [x]`、`- [X]` 和 `- [ ]` 沿用现有任务模型。已勾选且没有代码或测试支撑的任务是完整性缺口。
- **Rationale**: 宪章已经固定这三条证据规则。Spec Kit 的 `FR-###` 和勾选任务能够落到现有模型，不需要新的证据等级。
- **Alternatives considered**: 把用户故事标题的模糊匹配当成直接证据，会把推断写成实现。忽略 `tasks.md` 的勾选状态，就回答不了任务完整性。

## Decision: 语言范围保持 Java

- **Decision**: Maven 与 Gradle 的识别、构建和测试命令只用于 Java 服务端布局。Spec Kit 仓库如果不是这种布局，报告写明代码检查不支持，不猜测构建命令，也不给出代码风险或测试已经通过的结论。需求文件仍可被读取，但需求符合性不得标成通过。
- **Rationale**: 宪章把审核对象限制在 Java 服务端。支持 Spec Kit 解决的是需求文件放在哪里，不是突然审核任意语言。
- **Alternatives considered**: 让 SpecGuard 审核本仓库这样的 Python Spec Kit 项目，需要另一次宪章修订。把非 Java 仓库直接拒绝在发现目录之前，会少掉“布局已识别但不支持代码检查”的说明。

## Decision: 被审核仓库的宪章不是 SpecGuard 的策略

- **Decision**: 若所选功能的仓库含有 `.specify/memory/constitution.md`，报告的限制说明可以记录该文件存在。文件正文不进入审核策略，不覆盖建议模式，也不放进模型请求。
- **Rationale**: 被审核仓库里的文字是不可信输入。用它改写 SpecGuard 的阻断规则，会违反“源码和文档中的指示不得改写审核策略”。
- **Alternatives considered**: 把对方宪章的 MUST 当成阻断条件，会让被审核项目决定 SpecGuard 的退出码。
