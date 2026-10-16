# Contract: 配置文件

文件名默认为仓库根目录的 `specguard.yaml`。加载失败时命令在检查开始前退出 `4`，并指出字段路径。未识别的功能字段必须报错，不能静默忽略。

## 顶层

| 字段 | 必需 | 含义 |
| --- | --- | --- |
| version | 是 | 配置结构版本。v0.1 只接受 `1` |
| project.root | 否 | 项目根，默认当前目录 |
| openspec.root | 否 | OpenSpec 目录，默认识别 `openspec/` |
| openspec.change | 否 | 默认变更名。为空且有多个变更时必须在命令行指定 |
| openspec.include_main_specs | 否 | 是否阅读长期规范，默认是 |
| openspec.require_change_selection | 否 | 多个变更时是否强制选择，默认是 |
| git.base | 是 | 基线版本 |
| git.target | 否 | 目标版本，默认 `HEAD` |
| git.include_worktree | 否 | 默认不纳入未提交改动 |
| git.fail_on_uncommitted_changes | 否 | 工作区不干净且未明确纳入时是否失败，默认是 |
| review.mode | 否 | `static` 或 `assisted`，默认 `static` |
| review.policy | 否 | `advisory` 或 `strict`，默认 `advisory` |
| review.dimensions | 否 | 四个维度的开关：需求、业务逻辑、测试、回归 |
| review.severity_thresholds.block_on | 否 | 严格策略下可阻断的严重程度 |
| review.llm_findings_block | 否 | v0.1 只接受 `false`。设为 `true` 时配置无效 |
| checks | 否 | 确定性检查，见下表 |
| llm | 条件 | `review.mode` 为 `assisted` 时必需 |
| security | 否 | 密钥遮盖、外网、输出上限、构建隔离 |
| report.formats | 否 | `markdown` 与 `json` 的子集，默认两者 |
| report.output_dir | 否 | 默认 `.specguard/reports` |
| report.include_source_snippets | 否 | 默认 `false` |

## 检查项

每个检查有 `enabled`、`required`，以及可选的 `command` 和 `timeout_seconds`。

| 检查 | v0.1 行为 |
| --- | --- |
| build | 启用且未给命令时，不猜测构建命令，结果为 `ERROR`（若 required）或 `SKIPPED` |
| tests | 同上 |
| checkstyle / spotbugs / pmd / jacoco / archunit | 可选适配器。工具不存在时非必需为 `SKIPPED`，必需为 `ERROR` |
| openspec_validate | 仅当本机有对应命令且启用时运行 |

`command` 必须落在实现维护的允许列表中：Maven wrapper 或 `mvn` 的构建与测试目标、Gradle wrapper 或 `gradle` 的对应任务，以及上述已命名工具。列表之外的命令使配置无效。

超时必须为正整数。输出摘要不得超过 `security.max_command_output_bytes`。

## 模型

| 字段 | 规则 |
| --- | --- |
| llm.enabled | `assisted` 模式下必须为真 |
| llm.provider | 只接受内网 OpenAI 兼容适配器 |
| llm.base_url | 必须显式给出。空值或外部回退地址使配置无效 |
| llm.model | 记录到报告元数据 |
| llm.api_key_env | 只保存环境变量名，不把密钥写入配置或报告 |
| llm.external_fallback | 只接受 `false` |
| llm.timeout_seconds / max_retries / max_context_chars | 必须为正，重试次数不得无限 |

`security.external_network` 默认为 `false`。为 `false` 时，除显式 `base_url` 外不发起审核用的网络请求。

## 路径

`report.output_dir` 解析后必须仍在允许的报告根内。包含 `..` 逃逸、指向源文件或指向 Git 元数据的路径，校验失败并退出 `4`。
