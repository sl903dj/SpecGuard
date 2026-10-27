# 安装之后怎么使用 SpecGuard

本文从命令已经装好开始。空目录只用于安装验证，不是审核地点，命令也不往里面写文件。审核在被审核仓库里运行。

SpecGuard 是只读质量门。它回答需求符合性、任务完整性、代码风险、测试有效性和审核效率。是否接受变更由工程师决定。默认策略是建议模式，不阻止合并。

## 1. 确认命令

在任意目录运行：

```bash
specguard version
specguard --help
```

成功时退出码为 `0`。`specguard version` 的标准输出只有 `0.4.0`。这两条命令不读仓库，也不写报告。

命令找不到时，先回到 [安装说明](install.md)，不要继续审核。下一步进入被审核仓库。

## 2. 进入被审核仓库

`cd` 到含有 `.git` 的 Java 仓库根目录。不要把 SpecGuard 源码克隆进这个仓库。

当前目录就是该仓库根时，可以继续。不在版本库中时，审核退出 `4`，提示「当前目录不在版本库中。请在 Git 仓库内运行审核。」并且不执行构建。下一步确认需求工件。

## 3. 确认需求工件

OpenSpec 进行中的变更位于 `openspec/changes/<变更名>/`。从零建立的当前规范位于 `openspec/specs/<能力>/spec.md`，需求使用普通的 `### Requirement:`，不使用 ADDED、MODIFIED、REMOVED。Spec Kit 功能位于 `specs/<功能目录>/`，至少需要 `spec.md`，通常还包含 `plan.md` 和 `tasks.md`。

Spec Kit 的选择优先级是 `--subject`、`artifacts.subject`、`.specify/feature.json`。三者都没有时退出 `4`，即使仓库里只有一个功能目录也不会自动选中，并且不运行检查、模型或报告写入。OpenSpec 的 `--change` 仍可用，但只作为 OpenSpec 兼容别名；不要与不同值的 `--subject` 混用。

## 4. 编写最小配置

在仓库根创建 `specguard.yaml`。v0.1 至少包含：

```yaml
version: 1
artifacts:
  provider: speckit
  root: specs
  subject: 003-example
git:
  base: main
```

上面的 `main` 只是例子。把 `git.base` 换成该仓库能解析的分支、标签或提交。无法解析时退出 `4`，不改用 `HEAD`。

其余字段用产品默认值：目标 `HEAD`，模式 `static`，策略 `advisory`，报告同时输出 Markdown 和 JSON。需要构建或测试时再增加允许列表内的命令，例如 `./mvnw` 或 `./gradlew`。不写命令时，启用且必需的检查为 `ERROR`，非必需为 `SKIPPED`。`review.llm_findings_block` 和 `llm.external_fallback` 保持 `false`。

文件位于仓库根即可进入校验。字段无法识别或基线写错时，下一步会退出 `4`。

完整三档见 [docs/config-templates.md](config-templates.md)。最小档只适合不跑构建的审核。需要构建和测试时复制标准档。本机有静态分析工具时复制推荐档。

## 5. 校验配置

```bash
specguard config validate --config specguard.yaml
```

`--config` 必须显式传入。

成功时退出码为 `0`，标准输出为「配置可用」。不写报告，不联系模型。失败时退出码为 `4`，指出无效字段，不开始审核。下一步处理未提交改动。

## 6. 处理未提交改动

默认不审核脏工作区。仍有未提交改动时停止审核。

工作区干净，或你明确决定纳入未提交改动时，可以继续。仍有未提交改动时，审核退出 `4`，提示「工作区有未提交改动。未明确纳入时停止审核。」只审已提交差异时，先提交再运行。要把未提交改动一并纳入时，在下一步加上 `--include-worktree`。报告会把它们与已提交变更区分开。下一步运行静态建议审核。

## 7. 运行一次静态建议审核

在仓库根运行：

```bash
specguard review --config specguard.yaml --mode static --policy advisory
```

Spec Kit 可加 `--subject <功能目录>`；OpenSpec 旧调用可继续使用 `--change <变更名>`。审核整份当前规范时加上 `--baseline`，或在配置里写 `artifacts.subject_kind: current`。`--baseline` 与 `--change` 不能同时使用。仓库同时有当前规范和进行中的变更、又没有明确选择时，退出 `4`。基线与配置不同时加上 `--base <版本>`。

成功时，标准输出是报告文件路径。默认文件是 `.specguard/reports/<变更名>-<目标提交前 12 位>.md` 和同名 `.json`。建议模式下，报告里可以有 `FAIL`，进程仍退出 `0`。这次审核对仓库的写入只有报告目录。用法或配置问题退出 `4`。必需检查未完成时退出 `3`，这不是干净通过。下一步阅读报告。

## 8. 阅读报告

先看 Markdown 的整次状态、需要人工审核、需求覆盖、潜在风险、证据定位、检查结果和限制说明。状态词、证据级别和退出码的含义见 [docs/report-interpretation.md](report-interpretation.md)，这里不另写一套定义。

退出码 `0` 表示完成且未阻断。退出码 `2` 只在后文可选的严格步骤里、并且命中已确认的确定性失败时出现。退出码 `3` 表示必需检查未完成。同时满足阻断和不完整时取 `3`。缺少测试证据不是代码一定有错。没有发现也不是代码安全。

你能指出每条结论的证据，或看到证据不足，就可以进入下一步。不要把退出码 `0` 当成代码安全，也不要把证据不足当成代码一定有错。

## 9. 由工程师决定

SpecGuard 不接受、不拒绝、也不合并变更。是否接受由工程师决定。

## 可选的后续步骤

第一次使用到第 9 步结束。下面两步可选，不是必经步骤。

把第 7 步的 `--policy advisory` 换成 `--policy strict` 时，只有已确认的确定性失败才会退出 `2`。模型假设不单独造成阻断。

辅助审查必须先在配置里启用 `llm` 并填写内网 `llm.base_url`，再使用 `--mode assisted`。未配置模型时保持静态模式。内网地址的限制、密钥变量、模型不可用时怎么读报告，以及按退出码排障和持续集成，写在 [docs/operations.md](operations.md)。

## v0.2 迁移

旧的 `openspec` 配置无需修改。新配置推荐使用中立的 `artifacts`；同时提供两套配置时，provider、root 和 subject 必须一致。JSON 报告升级为 schema `1.1`，新增 `artifact_provider`、`subject_id`、`selection_source` 和上下文清单；旧的 `metadata.change` 与 `artifacts.selected_change` 仍保留。

## v0.3 当前规范

`subject_kind: current` 不能再写变更名。只写旧的 `openspec.change` 时，行为仍是变更审核。当前规范报告的 `metadata.change` 和 `artifacts.selected_change` 为空，`tasks_available` 为 `false`，Markdown 写明「任务完整性不可用」。schema 为 `1.2`，1.1 的字段名仍然保留。

## v0.4 证据与对照

报告 schema 为 `1.3`。1.2 的对象种类、任务可用性和兼容字段仍然保留。

证据范围默认是 `range`，只使用 `git.base` 到 `git.target` 的差异。`--evidence-scope target-tree` 或 `git.evidence_scope: target_tree` 只适用于当前 OpenSpec：它读取目标版本的文件内容来找需求证据，不把整棵树记成差异。用在变更或 Spec Kit 上时，审核在检查开始前退出 `4`，并说明「完整内容证据范围只适用于当前规范」。

直接证据只表示找到了需求标识，不表示验收场景已经通过。推断关联不能单独证明需求已经实现。没有线索时写明找不到实现证据。场景会单独给出已有测试支撑、覆盖缺口或场景审核不可用。

审核 OpenSpec 变更时，会对照 `openspec/specs/` 里的当前规范。未声明的对立场景会写出两边的来源位置。已声明的修改或删除不记成冲突。当前规范里变更没有提到的需求不会并进变更清单。没有当前规范时写明「规范对照不可用」。审核当前规范或 Spec Kit 时写明「未做 OpenSpec 当前规范对照」。

历史对照读取报告目录里的 `calibration.json`，由工程师维护。记录缺失或不完整时，报告写明「历史对照未完成」。没有完整历史审核却把 `complete` 标成 true 时，完成标记会被拒绝。完成对照不会打开阻断或自动合并。辅助审查的假设仍然不阻断。

每次报告都会列出九类风险：`boundary`、`exception`、`null_empty`、`transaction`、`concurrency`、`authorization`、`compatibility`、`persisted_data`、`dependency_config`。有真实行号和失败路径时记为发现；否则记为缺少上下文。已检查不等于代码安全。

一次变更碰到多个构建模块、而构建或测试命令按整个仓库配置时，报告点名这些模块，并增加一条状态为 `SKIPPED`、命令为空的 `module-separation` 检查。程序不会另编按模块执行的命令。无法识别布局时只说明限制。
