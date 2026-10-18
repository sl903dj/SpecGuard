# Contract: 命令行

SpecGuard 是本地只读命令。使用者安装 `specguard` 到命令路径，在被审核仓库里运行；该仓库不需要包含 SpecGuard 源码。包不在 PyPI。能访问 GitHub 时，安装命令是 `uv tool install "git+https://github.com/sl903dj/SpecGuard"`。不能访问 GitHub 或 PyPI 时，用手工传入的检出根目录和依赖轮子目录执行 `uv tool install --offline --no-index --find-links <轮子目录> <检出根目录>`。检出根目录含有 `pyproject.toml`，不是 `src/specguard`。直接依赖是 `typer>=0.12`、`pydantic>=2`、`httpx>=0.27`、`pyyaml>=6`。轮子目录还包含传递依赖和构建依赖 `setuptools>=68`。验证时先离开源码检出，到一个新建的空目录执行 `specguard version`。该目录不是安装位置，命令不往里面写文件。v0.1 的安装入口是 Python 控制台脚本，不要求单独的原生二进制。v0.1 不提供网页，也不替调用方合并代码。退出码是给人和以后的包装层看的信号。

## 命令

### `specguard version`

打印产品版本后退出。不读取仓库，不运行审核。

- **成功**: 退出码 `0`，标准输出只有版本信息。

### `specguard --help` 与子命令帮助

打印用法后退出。不运行审核。

- **成功**: 退出码 `0`。

### `specguard config validate [--config PATH]`

只校验配置。不运行检查，不联系模型。

- **成功**: 退出码 `0`，并说明配置可用。
- **失败**: 退出码 `4`，指出无效字段。不开始审核。

### `specguard review [选项]`

执行一次审核并写出报告。

| 选项 | 含义 | 默认 |
| --- | --- | --- |
| `--config PATH` | 配置文件 | 仓库根的 `specguard.yaml` |
| `--change NAME` | OpenSpec 变更名 | 配置中的变更；都没有且存在多个变更时失败 |
| `--base REV` | 基线版本 | 配置中的基线 |
| `--target REV` | 目标版本 | 配置中的目标，通常为 `HEAD` |
| `--include-worktree` | 纳入未提交改动 | 关闭 |
| `--mode static\|assisted` | 是否运行辅助审查 | 配置中的模式 |
| `--policy advisory\|strict` | 建议或严格 | 配置中的策略，产品默认为 `advisory` |
| `--format LIST` | `markdown`、`json` 或两者 | 两者 |
| `--output DIR` | 报告目录 | 配置中的目录 |

命令行显式参数覆盖配置文件。非法取值在任何检查之前失败。

## 退出码

| 码 | 名称 | 何时使用 |
| --- | --- | --- |
| 0 | OK | 审核完成且策略未阻断。报告里可以仍有发现 |
| 1 | INTERNAL | 未预期的程序错误 |
| 2 | POLICY_BLOCKED | 调用方明确选择严格策略，且命中允许阻断的确定性失败 |
| 3 | INCOMPLETE | 必需检查被跳过、出错、超时，或审核期间源状态已变化 |
| 4 | USAGE | 不是版本库、基线无法解析、配置无效、变更选择含糊，或报告路径非法 |

帮助和版本命令不使用 `2`、`3`、`4`。建议模式下，确定性失败仍退出 `0`，失败写在报告里。纯模型假设在任何模式下都不使退出码变成 `2`。

同时满足“必需检查未完成”和“严格策略命中失败”时，退出码取 `3`。报告仍列出已确认的失败，但整次状态保持 `REVIEW_INCOMPLETE`。

## 只读边界

`review` 对目标仓库允许的写入只有报告目录。它不修改业务源文件、OpenSpec 工件、Git 索引或提交历史，不执行提交、合并、发布，也不连接生产环境。

构建命令只来自配置允许列表。模型输出不能增加命令。

## 安装之后的使用顺序

`specguard version` 输出 `0.1.0` 只说明命令已安装。日常审核在被审核仓库里进行。安装验证用的空目录不是使用地点。`docs/usage.md` 按下列顺序书写。每一步都写命令、成功时的输出、失败时的退出码，以及下一步做什么。

1. **确认命令**。在任意目录运行 `specguard version` 和 `specguard --help`。期望退出码 `0`。版本命令的标准输出只有 `0.1.0`。这两条命令不读仓库，也不写报告。
2. **进入被审核仓库**。`cd` 到含有 `.git` 的 Java 仓库根目录。该仓库不克隆 SpecGuard 源码。不在版本库中时，`review` 退出 `4`，提示先在 Git 仓库内运行，并且不执行构建。
3. **确认 OpenSpec 变更**。进行中的变更位于 `openspec/changes/<变更名>/`，其中应有 `proposal.md`、`design.md`、`tasks.md`，需求在该目录下的 `specs/**/spec.md`。只有一个变更时可以不传 `--change`。多个变更且未选择时退出 `4`，列出变更名，不自动挑选。找不到 OpenSpec 时审核仍可继续，但报告写明基于需求的审核不可用，不得宣称需求符合性已通过。
4. **编写最小配置**。在仓库根创建 `specguard.yaml`。v0.1 至少包含：

```yaml
version: 1
git:
  base: main
```

`git.base` 换成该仓库能解析的分支、标签或提交。无法解析时退出 `4`，不改用 `HEAD`。其余字段用产品默认值：目标 `HEAD`，模式 `static`，策略 `advisory`，报告写到 `.specguard/reports`，同时输出 Markdown 和 JSON。需要构建或测试时再增加允许列表内的命令，例如 `./mvnw` 或 `./gradlew`。不写命令时，启用且必需的检查为 `ERROR`，非必需为 `SKIPPED`。`review.llm_findings_block` 和 `llm.external_fallback` 保持 `false`。
5. **校验配置**。运行 `specguard config validate --config specguard.yaml`。`--config` 必须显式传入。成功时退出 `0`，标准输出为「配置可用」，不写报告，不联系模型。失败时退出 `4`，指出无效字段，不开始审核。
6. **处理未提交改动**。默认不审核脏工作区。仍有未提交改动时，`review` 退出 `4`，提示未明确纳入时停止审核。只审已提交差异时，先提交再运行。要把未提交改动一并纳入时，加上 `--include-worktree`；报告必须把它们与已提交变更区分开。
7. **运行一次静态建议审核**。在仓库根运行：

```bash
specguard review --config specguard.yaml --mode static --policy advisory
```

多个变更时加上 `--change <变更名>`。基线与配置不同时加上 `--base <版本>`。成功启动后，标准输出是报告文件路径。默认文件是 `.specguard/reports/<变更名>-<目标提交前 12 位>.md` 和同名 `.json`。建议模式下，报告里可以有 `FAIL`，进程仍退出 `0`。这次审核对仓库的写入只有报告目录。
8. **阅读报告**。先看 Markdown 的整次状态、需要人工审核、需求覆盖、潜在风险、证据定位、检查结果和限制说明。状态词、证据级别和退出码的含义指向 `docs/report-interpretation.md`，使用说明不另写一套定义。退出码 `0` 表示完成且未阻断；`2` 只在稍后显式选择严格策略且命中确定性失败时出现；`3` 表示必需检查未完成；同时满足阻断和不完整时取 `3`。缺少测试证据不是代码一定有错。没有发现也不是代码安全。
9. **由工程师决定**。使用说明写明 SpecGuard 不接受、不拒绝、也不合并变更。

严格模式和内网辅助审查写在第 9 步之后，并标明可选，不作为第一次使用的必经步骤。严格模式是把第 7 步的 `--policy advisory` 换成 `--policy strict`。辅助审查必须先在配置里启用 `llm` 并填写内网 `llm.base_url`，再使用 `--mode assisted`。未配置模型时保持静态模式。
