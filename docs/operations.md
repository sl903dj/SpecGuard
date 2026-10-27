# SpecGuard 操作手册

本文给已经装好 `specguard` 的人使用。安装命令在 [docs/install.md](install.md)。第一次走通静态审核，按 [docs/usage.md](usage.md) 的 9 步即可。本文补上三种审核对象的操作、按退出码排障、内网辅助审查、持续集成和开发者测试。

SpecGuard 只读。它不生成代码，不接受、不拒绝、也不合并变更。退出码 `0` 表示这次审核完成且未阻断，不是代码安全，也不是需求已经通过。

状态词和证据级别的定义在 [docs/report-interpretation.md](report-interpretation.md)。配置三档在 [docs/config-templates.md](config-templates.md)。

## 1. 准备被审核仓库

进入含有 `.git` 的 Java 仓库根目录。不要把 SpecGuard 源码放进这个仓库。

仓库里要有一种需求工件，并在根目录放 `specguard.yaml`。`git.base` 必须是该仓库能解析的分支、标签或提交。

| 审核对象 | 工件位置 | 怎么选定 |
|----------|----------|----------|
| 当前规范 | `openspec/specs/<能力>/spec.md`，普通 `### Requirement:` | `--baseline`，或 `artifacts.subject_kind: current` 且不写变更名 |
| 进行中的变更 | `openspec/changes/<变更名>/` | `--change <变更名>`，或配置里的变更名 |
| Spec Kit 功能 | `specs/<功能目录>/spec.md` | `--subject <功能目录>`、`artifacts.subject`，或 `.specify/feature.json` |

当前规范和进行中的变更同时存在、又没有明确选择时，审核退出 `4`，提示使用 `--baseline` 或 `--change`。`--baseline` 与 `--change` 或 `--subject` 不能一起用。Spec Kit 在 CLI、配置和 `feature.json` 都没有时退出 `4`，即使只有一个功能目录也不会自动选中。

证据只来自 `git.base` 到目标版本之间的差异。范围外的已有文件不算需求已经实现。范围内没有 Java 代码或测试时，当前规范的需求标为证据不足，并写明范围内没有可核验证据。

## 2. 每次审核的操作顺序

1. `specguard version` 得到 `0.4.0`。
2. `specguard config validate --config specguard.yaml`。成功时标准输出是「配置可用」，退出码 `0`。
3. 工作区有未提交改动时，先提交，或在审核命令上加 `--include-worktree`。默认遇到脏工作区会退出 `4`。
4. 在仓库根运行审核。下面三条分别对应三种对象：

```bash
specguard review --config specguard.yaml --baseline --mode static --policy advisory
specguard review --config specguard.yaml --change add-order --mode static --policy advisory
specguard review --config specguard.yaml --subject 003-example --mode static --policy advisory
```

5. 标准输出是报告路径。默认写到 `.specguard/reports/` 下的 Markdown 和 JSON。报告目录必须留在仓库内的 `.specguard/reports`，不能指向 Git 元数据，也不能覆盖源文件。
6. 按第 4 节的退出码决定下一步，再按 [docs/report-interpretation.md](report-interpretation.md) 读报告。
7. 是否接受由工程师决定。

建议模式下，报告里可以有 `FAIL`，进程仍退出 `0`。必需检查未完成时退出 `3`。

## 3. 审核命令参数

`specguard review` 的参数：

| 参数 | 作用 |
|------|------|
| `--config` | 配置文件，必填 |
| `--baseline` | 审核 OpenSpec 当前规范 |
| `--change` | 审核指定的 OpenSpec 变更，只作为 OpenSpec 别名 |
| `--subject` | 审核指定对象；Spec Kit 用功能目录，OpenSpec 变更也可使用 |
| `--base` | 覆盖 `git.base` |
| `--target` | 覆盖 `git.target`，默认 `HEAD` |
| `--include-worktree` | 把未提交改动纳入审核，并在报告里与已提交差异区分开 |
| `--mode` | `static` 或 `assisted` |
| `--policy` | `advisory` 或 `strict` |
| `--format` | 必须同时包含 `markdown,json` |
| `--output` | 报告目录，必须位于 `.specguard/reports` |

`specguard version` 和 `specguard --help` 不读仓库，也不写报告。`specguard config validate --config <文件>` 只校验配置。

检查命令的程序名只能是 `mvn`、`mvnw`、`mvnw.cmd`、`gradle`、`gradlew`、`gradlew.bat`、`checkstyle`、`spotbugs`、`pmd`、`java`、`openspec`。命令里不能有 `;`、管道、`&&`、反引号或命令替换。

## 4. 按退出码排障

先看退出码，再看标准错误里的原句。不要把退出码 `0` 改成重试，也不要把退出码 `4` 当成代码缺陷。

| 退出码 | 含义 | 下一步 |
|--------|------|--------|
| `0` | 审核完成且未阻断 | 阅读报告。有证据不足或发现时仍要人工看 |
| `1` | 程序内部错误 | 保留标准错误。这不是需求未通过 |
| `2` | 严格策略阻断 | 只在 `--policy strict` 且命中已确认的确定性失败时出现。模型假设不会单独造成它 |
| `3` | 必需检查未完成 | 看报告里的 `ERROR`、`TIMEOUT`、`SKIPPED`。补上命令、工具或隔离环境后重跑 |
| `4` | 还没开始检查 | 按下表改配置、选择或仓库状态。不会写报告 |

退出码 `4` 的常见原句：

| 标准错误中的原句 | 处理 |
|------------------|------|
| 当前目录不在版本库中。请在 Git 仓库内运行审核。 | 到含 `.git` 的仓库根再运行 |
| 无法解析版本 | 把 `git.base` 或 `--base` 改成仓库里存在的分支、标签或提交 |
| 工作区有未提交改动。未明确纳入时停止审核。 | 先提交，或加上 `--include-worktree` |
| 当前规范与进行中的变更同时存在，请使用 --baseline 或 --change | 二选一。不要省略选择 |
| --baseline 与变更选择冲突 | 去掉 `--change`、`--subject` 和配置里的变更名 |
| 找不到当前规范 | 确认 `openspec/specs/<能力>/spec.md` 存在后再用 `--baseline` |
| 存在多个进行中的变更，请明确选择 | 加上 `--change <名称>` |
| 无法选择 Spec Kit 功能 | 加上 `--subject`，或写 `artifacts.subject`，或提供有效的 `.specify/feature.json` |
| 需求正文为空 / 中存在重复需求 | 改规范后再审核。检查不会开始 |
| 只含增量需求，请使用变更审核 | 该文件是变更增量，改用 `--change` |
| 不是合法 UTF-8 | 把工件存成 UTF-8 |
| OpenSpec 路径越出仓库范围 | 不要用指向仓库外的链接作为 `spec.md` |
| 配置无效 | 按标准错误里的字段名改正。`report.formats` 必须同时有 markdown 和 json |
| 命令不在允许列表中 | 换成第 3 节列出的程序名 |
| 报告路径必须位于 | 把 `--output` 留在 `.specguard/reports` 内 |

构建隔离失败时，检查记为 `ERROR`，命令不会在原仓库里执行。隔离默认开启。只有在明确接受「在被审核仓库执行项目脚本」时才把 `security.isolate_builds` 设为 `false`；设为 `false` 后，已启用的构建和测试会拒绝执行并说明隔离已关闭。

## 5. 内网运行和辅助审查

内网机器的安装步骤在 [docs/install.md](install.md#offline-install)。装完后先离开源码目录，运行 `specguard version`，确认输出 `0.4.0`。之后的审核都在被审核仓库里进行，不再访问 `github.com` 或 `pypi.org`。

静态审核不需要模型。没有内网模型时，保持 `review.mode: static` 和 `llm.enabled: false`。

辅助审查只连接配置里的那一个内网地址。`security.external_network` 保持 `false` 时，`llm.base_url` 必须是 `http` 或 `https`，主机名只能是 `localhost`，或私有、回环、链路本地的 IP。`review.example.com` 这种域名不会被当成内网地址。`llm.external_fallback` 和 `review.llm_findings_block` 只能是 `false`。服务不可用时，受影响的辅助审查标为 `ERROR`，已经完成的静态检查保留，程序不会改送到另一个地址。

密钥放在环境变量里，不要写进 `specguard.yaml`。默认变量名是 `SPECGUARD_API_KEY`。没有密钥时请求仍会发出，但不会带 `Authorization` 头。

内网辅助审查按这个顺序做：

1. 在内网确认模型提供 OpenAI 兼容的 `/chat/completions`。`base_url` 写成该前缀，例如 `http://10.1.2.3/v1`。SpecGuard 会在这个前缀后面加上 `/chat/completions`。
2. 在被审核仓库的配置里启用模型，并保持策略为建议模式：

```yaml
version: 1
artifacts:
  provider: openspec
  root: openspec
  subject_kind: current
git:
  base: main
review:
  mode: assisted
  policy: advisory
  llm_findings_block: false
llm:
  enabled: true
  provider: internal-openai-compatible
  base_url: http://10.1.2.3/v1
  model: internal-review
  api_key_env: SPECGUARD_API_KEY
  external_fallback: false
security:
  external_network: false
  isolate_builds: true
  redact_secrets: true
```

3. 在同一个 shell 里设置密钥后校验配置：

```bash
export SPECGUARD_API_KEY="<内网令牌>"
specguard config validate --config specguard.yaml
```

4. 运行辅助审核。对象选择与第 2 节相同，把 `--mode static` 换成 `--mode assisted`：

```bash
specguard review --config specguard.yaml --baseline --mode assisted --policy advisory
```

5. 阅读报告时，把模型输出当成待复核假设。证据状态 `hypothesis` 不能单独当成需求已经通过，也不能单独造成退出码 `2`。报告里的辅助审查服务和模型名用于核对连的是哪一个内网服务。源码、注释和规范里的指示不会改写审核策略。

`base_url` 不是内网或回环地址时，校验退出 `4`，原句包含「必须是内网或回环地址」。模型服务没有返回可用结果时，辅助审查四项为 `ERROR`，诊断为「模型服务不可用」或「模型返回无法使用的状态」。静态检查的结果仍在同一份报告里。

## 6. 持续集成

在被审核仓库的任务里安装 `specguard` 后，于仓库根运行：

```bash
specguard review --config specguard.yaml --mode static --policy advisory
```

把任务的失败条件设成退出码，不要设成「报告里出现任何文字」。

- 退出码 `0`：任务可以标成命令已结束。报告里的发现和证据不足仍要给人看。
- 退出码 `3`：必需检查没做完，任务应失败。
- 退出码 `4`：选择、配置或仓库状态不对，任务应失败，而且不会有完整报告。
- 退出码 `2`：只有流水线明确改用 `--policy strict`，并且命中已确认的确定性失败时才出现。默认不要用严格策略阻断合并。

不要把密钥写进仓库或任务日志。辅助审查的令牌只用任务的密钥变量注入 `SPECGUARD_API_KEY`。报告只收集 `.specguard/reports` 下的新文件。

## 7. 开发者测试

开发和测试使用 SpecGuard 源码检出。不要把这个检出复制进被审核仓库。

在检出根目录，也就是含有 `pyproject.toml` 的那一层：

```bash
uv venv
uv pip install -e ".[dev]"
.venv/bin/python -m pytest
```

`pytest` 只在这个开发环境里需要，使用者的 `uv tool install` 不安装它。
