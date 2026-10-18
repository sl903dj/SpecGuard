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
