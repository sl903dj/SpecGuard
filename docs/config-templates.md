# SpecGuard 配置模板

选择下面一档，把 `git.base` 换成该仓库能解析的分支、标签或提交，再复制为仓库根的 `specguard.yaml`。命令不自动加载本文档。三档都是静态模式和建议策略。

## 最小

不启用检查。只审核 OpenSpec 与 Git 差异能得到的证据。这一档只适合不跑构建的审核。

```yaml
version: 1
git:
  base: main
  target: HEAD
review:
  mode: static
  policy: advisory
  llm_findings_block: false
llm:
  enabled: false
  external_fallback: false
```

## 标准

在最小档上启用并要求构建和测试。构建超时 600 秒，测试超时 900 秒。构建在隔离副本中运行。

```yaml
version: 1
git:
  base: main
  target: HEAD
review:
  mode: static
  policy: advisory
  llm_findings_block: false
checks:
  build:
    enabled: true
    required: true
    command: "./mvnw -q -DskipTests package"
    timeout_seconds: 600
  tests:
    enabled: true
    required: true
    command: "./mvnw -q test"
    timeout_seconds: 900
llm:
  enabled: false
  external_fallback: false
security:
  isolate_builds: true
  external_network: false
  redact_secrets: true
report:
  formats:
    - markdown
    - json
  output_dir: .specguard/reports
  include_source_snippets: false
```

Gradle 仓库把这两条命令换成 `./gradlew assemble` 和 `./gradlew test`。不要在同一份文件里同时留下 Maven 和 Gradle 命令。

## 推荐

包含标准档的全部字段，并增加三项非必需静态检查。本机有这些工具时复制这一档。程序名必须是允许列表中的 `checkstyle`、`spotbugs`、`pmd`。工具不存在时该检查为 `SKIPPED`。团队若要追加参数，程序名保持不变。

```yaml
version: 1
git:
  base: main
  target: HEAD
review:
  mode: static
  policy: advisory
  llm_findings_block: false
checks:
  build:
    enabled: true
    required: true
    command: "./mvnw -q -DskipTests package"
    timeout_seconds: 600
  tests:
    enabled: true
    required: true
    command: "./mvnw -q test"
    timeout_seconds: 900
  checkstyle:
    enabled: true
    required: false
    command: checkstyle
    timeout_seconds: 600
  spotbugs:
    enabled: true
    required: false
    command: spotbugs
    timeout_seconds: 600
  pmd:
    enabled: true
    required: false
    command: pmd
    timeout_seconds: 600
llm:
  enabled: false
  external_fallback: false
security:
  isolate_builds: true
  external_network: false
  redact_secrets: true
report:
  formats:
    - markdown
    - json
  output_dir: .specguard/reports
  include_source_snippets: false
```

JaCoCo 和 ArchUnit 不列入推荐档。`jacoco` 和 `archunit` 不是允许的命令程序名。
