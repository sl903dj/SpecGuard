# Research: SpecGuard 变更质量守卫

本文件把实现计划里的技术选择固定下来。规格本身不规定实现技术；这些决定来自 SpecGuard v0.1 设计包，并对照宪章做了取舍。没有遗留的 `NEEDS CLARIFICATION`。

## Decision: 使用者安装命令，不在被审核仓库里拉取源码

- **Decision**: SpecGuard 的使用方式对齐本机已安装的 Spec Kit `specify` 1.2.0。使用者得到 PATH 上的 `specguard` 命令，然后在 Java 仓库的工作目录里运行。被审核仓库不包含 SpecGuard 的 Git 检出。v0.1 的安装形态是 Python 控制台脚本，由安装器放到命令路径；不把单个原生二进制列为必须交付。SpecGuard 的开发、测试和打包仍在本仓库的源码检出中完成。
- **Rationale**: 本机的 `specify` 是 `~/.local/bin/specify`，指向 uv 工具环境里的 Python 入口脚本，不是把 Spec Kit 源码克隆进当前项目后再运行。审核工具若要求先克隆再运行，就会把工具源码混进被审核仓库，和只读质量门的用法相反。
- **Alternatives considered**: 要求 `git clone` 后在源码树里运行，只适合 SpecGuard 开发者。用 Go 或打包器做成单个原生二进制可以去掉对 Python 的依赖，但 Spec Kit 本身也不是这种二进制，v0.1 没有额外理由更换实现语言。

## Decision: 从 GitHub 安装，不用 PyPI 包名

- **Decision**: `specguard` 没有发布到 PyPI。使用者安装命令是 `uv tool install "git+https://github.com/sl903dj/SpecGuard"`。安装器把仓库拉进 uv 的工具环境，不把检出放进被审核仓库。验证本地源码能否安装：在源码检出上执行 `uv tool install --force <本仓库绝对路径>`，然后进入一个新建的、不含 `src/specguard` 的目录，运行 `specguard version`。期望退出码为 0，输出 `0.1.0`。
- **Rationale**: `uv tool install specguard` 会向默认索引查找包名。包不在 PyPI 时这条命令失败，不能写成安装说明。从 Git 地址安装与 Spec Kit 的 uv 工具安装方式相同，同时保留“被审核仓库里没有 SpecGuard 源码”的边界。本地路径安装使用同一安装器，用来在远程还不存在时证明控制台脚本可以被装上并在源码树外运行。
- **Alternatives considered**: 继续写 `uv tool install specguard` 会被索引拒绝。先发布到 PyPI 才能使用包名，但 v0.1 没有选定公开索引。只在源码树里用 `python -m specguard` 不能证明命令已安装到 PATH。`--editable` 安装仍指向源码目录，不能代替一次非可编辑安装。

## Decision: 用空目录验证命令不依赖源码检出

- **Decision**: 安装完成后，先执行 `mkdir -p /tmp/specguard-install-check` 和 `cd /tmp/specguard-install-check`，再运行 `specguard version`。这个目录在运行前是空的，而且保持为空。它是当前工作目录，不是安装位置，也不是报告目录。`docs/install.md` 必须在这两条命令前写明：目的是离开 SpecGuard 源码检出，确认已安装的命令不依赖当前目录里有 `src/specguard`。本地源码验证和内网离线安装都使用同一说明。
- **Rationale**: `uv tool install` 把命令放到命令路径。如果仍站在检出目录里运行 `specguard version`，成功不能区分「命令已安装」和「因为当前目录就是源码树」。空目录排除后一种情况。`specguard version` 不读取也不写入当前目录。
- **Alternatives considered**: 删掉这两条命令，只在源码目录里运行版本命令，无法证明命令可以在被审核仓库里使用。把空目录写成安装输出目录，和 `uv tool install` 的实际行为不符。

## Decision: 内网电脑用手工传入的源码和依赖离线安装

- **Decision**: 不能访问 GitHub 或 PyPI 的内网电脑不执行 `uv tool install "git+https://github.com/sl903dj/SpecGuard"`。在一台能访问外网的电脑上克隆 `https://github.com/sl903dj/SpecGuard.git`，导出运行时依赖并下载成轮子目录，再额外下载 `setuptools>=68`。把检出根目录和轮子目录手工拷进内网。内网安装命令是 `uv tool install --offline --no-index --find-links <轮子目录> <检出根目录>`。`<检出根目录>` 是含有 `pyproject.toml` 的克隆目录，不是 `src/specguard`。装好后到一个不含 `src/specguard` 的目录运行 `specguard version`，期望输出 `0.1.0`。`docs/install.md` 列出直接依赖 `typer>=0.12`、`pydantic>=2`、`httpx>=0.27`、`pyyaml>=6`，并列出构建依赖 `setuptools>=68`。轮子目录必须同时包含运行时传递依赖和 `setuptools`。`pytest` 是开发依赖，安装命令时不需要。内网机预先具备 Python 3.11 或更高版本以及 `uv`。中英文 README 指向 `docs/install.md` 的离线安装一节。
- **Rationale**: 内网机访问不了 `github.com` 时，Git 地址安装会失败。只拷源码仍会在安装时向 PyPI 要 Typer、Pydantic、httpx 和 PyYAML。`--offline` 禁止网络，`--no-index` 不使用默认索引，`--find-links` 只使用手工传入的轮子目录。`uv export --no-dev --no-emit-project` 不包含 `[build-system] requires`。从检出根目录安装会本地构建，缺少 `setuptools>=68` 时离线解析失败。`src/specguard` 没有 `pyproject.toml`，传给 `uv tool install` 会被拒绝。
- **Alternatives considered**: 继续只写 GitHub 地址，内网机无法执行。把包发布到 PyPI 仍要外网。在外网先 `uv build --wheel`、内网只安装 wheel，可以不携带 `setuptools`，但当前流程仍从检出根目录安装，所以轮子目录要带上构建依赖。把 `src/specguard` 当作项目目录会安装失败。把 SpecGuard 源码克隆进被审核仓库，违反使用边界。

## Decision: 仓库根目录提供中英文 README

- **Decision**: GitHub 默认展示中文 `README.md`。英文为同级的 `README.en.md`。两份文件文首互相链接，章节一一对应：产品是只读质量门而不是编程助手；它回答需求符合性、任务完整性、代码风险、测试有效性和审核效率；安装使用 `uv tool install "git+https://github.com/sl903dj/SpecGuard"`，不用 PyPI 包名；本地源码用绝对路径安装后，在不含 `src/specguard` 的目录运行 `specguard version`；审核在被审核仓库中运行。详细步骤指向 `docs/install.md` 和 `specs/001-specguard-quality-gate/quickstart.md`，不复制命令契约和报告契约全文。
- **Rationale**: 仓库里的规格和计划是中文，GitHub 首页用中文可以直接阅读。单独的英文文件让英文读者不用在同一页里切换语言。两份文件保持同一结构，避免一边多写一边漏写安装限制。
- **Alternatives considered**: 只写一份双语 README 会让 GitHub 首页变长，也更难保持两边同步。只写英文 README 和现有中文规格脱节。把 `docs/install.md` 当作 README 不能出现在 GitHub 仓库首页。

## Decision: 仓库许可证使用 Apache-2.0

- **Decision**: 版权持有人选择 Apache-2.0。根目录 `LICENSE` 使用 Apache License 2.0 标准文本，版权行写 `Copyright 2026 sl903dj`。`pyproject.toml` 设置 `license = "Apache-2.0"`。中英文 README 都链接到 `LICENSE`，并写明许可证名称。不另写 `NOTICE`，当前没有需要单独署名的第三方声明。
- **Rationale**: 许可证必须由版权持有人指定。选定之后，仓库首页、打包元数据和许可证正文使用同一个 SPDX 标识，避免 README 和包元数据各写一套。
- **Alternatives considered**: MIT、BSD-2-Clause、GPL-3.0-only 和保留所有权利已提出但未选用。Spec Kit 扩展元数据里的 MIT 不是 SpecGuard 的许可。

## Decision: 把功能分支快进合并到 master 并推送

- **Decision**: 维护者把 `001-specguard-quality-gate` 合并进本地 `master`。`master` 没有功能分支之外的提交，所以使用快进合并。然后把 `master` 推送到 `origin`（`https://github.com/sl903dj/SpecGuard.git`）。不使用 `--force`。功能分支保留，后续 Spec Kit 命令仍在该分支上继续。
- **Rationale**: 合并前 GitHub 上的 `master` 停在 `3734e02`，默认分支看不到已完成的安装说明、README 和许可证。快进合并保持历史一条直线。合并和推送完成后，本地 `master` 与 `origin/master` 都指向 `b5d0d06`。宪章禁止的是 SpecGuard 自动合并被审核项目，不是维护者集成 SpecGuard 自己的仓库。
- **Alternatives considered**: 只推送功能分支会让 `master` 继续落后。强制推送会改写已经公开的 `master`。在产品里增加合并被审核仓库的命令，违反只读质量门原则。

## Decision: 用 Python 3.11 实现只读 CLI

- **Decision**: SpecGuard 本体使用 Python 3.11 或更高版本，作为本地命令行工具发布。审核对象仍是 Java / Spring Boot 仓库，SpecGuard 不因此改用 Java。
- **Rationale**: 审核流程主要是解析文本、调用现有构建工具和写出报告。Python 适合这种胶水型只读工具，也便于先写测试再实现。3.11 是设计包给出的下限，并提供可用的标准库子进程与路径处理。
- **Alternatives considered**: 用 Java 实现可以靠近被审核项目，但会把审核工具和业务构建绑在一起，也更重。用 Go 可以得到单个二进制，却没有足够理由放弃设计包已经选定、且更利于快速迭代解析逻辑的 Python。

## Decision: Typer 提供命令，Pydantic v2 承载配置与报告

- **Decision**: 命令入口使用 Typer。配置、检查结果、发现和报告使用 Pydantic v2 模型，并在加载时拒绝未知或非法字段。
- **Rationale**: 宪章要求配置无效时在执行检查前停止，并指出无效设置。类型模型可以把这条规则变成加载失败，而不是运行到一半再猜测。报告模型同时约束人类可读报告和结构化报告使用同一套结论。
- **Alternatives considered**: 只用 `argparse` 加手写字典更少依赖，但配置和报告字段多，手写校验容易漏掉“未支持的配置必须报错”。具体依赖版本在实现时对照内网环境锁定，不在本计划中猜一个未验证的版本号。

## Decision: 用 pytest，并且先写失败测试

- **Decision**: 单元测试和集成测试都使用 pytest。每个行为先有失败测试，再写实现。夹具覆盖合法变更、缺失工件、畸形工件、重命名、删除、非法版本和未提交改动。
- **Rationale**: 宪章禁止靠删除测试或削弱断言获得通过。审核工具自己的结论如果没有测试支撑，就违反它要求别人遵守的规则。
- **Alternatives considered**: 只做手工样例仓库不能覆盖退出码、超时和状态枚举。样例仓库仍然需要，但作为集成夹具，不代替自动化测试。

## Decision: 通过 Git 命令只读访问版本库

- **Decision**: 使用本机 `git` 可执行文件完成根目录识别、版本解析、差异、重命名和状态读取。允许的命令限于 `rev-parse`、`status`、`diff`、`log` 和 `show` 一类只读操作。不执行 `add`、`commit`、`checkout`、`reset`、`merge` 或 `clean`。
- **Rationale**: 重命名和版本解析已经由 Git 实现。再嵌入另一套 Git 库会增加偏差。只读命令清单是宪章“不改版本索引和提交历史”的可测试边界。
- **Alternatives considered**: 直接读 `.git` 对象更少进程，但容易读错索引并在实现时误写。libgit2 绑定增加原生依赖，却不能减少必须保持只读的义务。

## Decision: 人类可读报告使用 Markdown，结构化报告使用版本化 JSON

- **Decision**: 默认同一次审核写出 Markdown 和 JSON。JSON 带 `schema_version`。两种报告来自同一个报告模型。Markdown 包含“需要人工审核、需求覆盖、潜在风险、证据定位”和固定免责声明。
- **Rationale**: 规格要求一份供人阅读、一份供后续工具读取，且结构在同一产品版本内稳定。Markdown 可以直接放进拉取请求；JSON 让以后的持续集成包装层不必解析散文。
- **Alternatives considered**: 只产 Markdown 会让后续工具重新猜测结论。只产 JSON 则工程师不能直接审核。HTML 报告对 v0.1 没有额外价值。

## Decision: 一次审核的状态只留在内存，报告写成文件

- **Decision**: v0.1 不使用数据库。发现、证据和检查结果在单次进程内保存。报告默认写到被审核仓库中的 `.specguard/reports/`，且必须通过路径校验，不能覆盖源文件或逃出允许的报告目录。
- **Rationale**: 宪章要求更复杂的设计说明为什么简单做法不够。单次审核不需要跨次查询。文件报告已经满足复核和留存。
- **Alternatives considered**: 数据库能保存历史审核，但 v0.1 的成功标准是一次变更一份可复核报告，不是审核平台。历史对照由团队在试点时另行记录。

## Decision: 确定性检查先运行，命令来自受信任配置

- **Decision**: 检查执行器使用子进程，记录命令、耗时、退出状态，并截断输出。超时后终止该进程组。状态只允许 `PASS`、`FAIL`、`SKIPPED`、`ERROR`、`TIMEOUT`。构建和测试命令必须出现在配置的允许列表中，不能来自模型输出。工具不存在时，非必需检查为 `SKIPPED`，必需检查为 `ERROR`，两者都不是 `PASS`。
- **Rationale**: 宪章要求检查状态诚实，并且确定性检查先于辅助审查。允许列表挡住“模型生成任意命令”。
- **Alternatives considered**: 用壳字符串拼接命令实现更快，但会把注入和误执行带进审核工具。发现工具缺失时默默跳过并给整次审核打通过，直接违反宪章。

## Decision: Java 项目只识别 Maven 与 Gradle，并执行已配置命令

- **Decision**: 识别 `pom.xml`、`build.gradle`、`build.gradle.kts` 以及对应的 wrapper。报告发现到的模块。只有配置里写明且位于允许列表中的命令才会执行。无法识别布局时说明限制，并仍可执行明确配置的命令。Checkstyle、SpotBugs、PMD、JaCoCo、ArchUnit 和 `openspec validate` 都是可选适配器。
- **Rationale**: v0.1 的审核对象是 Java 服务端仓库。SpecGuard 不替换这些工具，只收集它们的结果并标出未执行。
- **Alternatives considered**: 自动猜测 `mvn test` 或 `gradle test` 能少写配置，但企业仓库依赖内网构件库和特殊参数，猜错的命令会被误记成产品失败。未配置时构建和测试检查标为需要配置，而不是偷偷执行。

## Decision: OpenSpec 由 SpecGuard 自己解析，不修改其工件

- **Decision**: 从配置或向上查找定位 `openspec/`。解析所选变更的 `proposal.md`、`design.md`、`tasks.md` 和 `specs/**/spec.md`，识别 `ADDED`、`MODIFIED`、`REMOVED` 需求、场景和任务勾选。保留源文件和行号。多个进行中变更且未选择时失败退出。没有 OpenSpec 时，需求审核标为不可用，不宣称符合性通过。
- **Rationale**: 规格要求只读发现需求，并在含糊时要求人工选择。自己解析 Markdown 不依赖某个 OpenSpec CLI 版本；可选的 `openspec validate` 只在本机可用且配置开启时运行。
- **Alternatives considered**: 把 OpenSpec CLI 当作硬依赖会让没有该命令的仓库无法做任何审核。修改或归档 OpenSpec 变更则违反只读原则。

## Decision: 追溯使用显式引用加有限启发式，并保留不确定性

- **Decision**: 需求、任务、变更文件和测试之间的关联分三级：`direct`、`inferred`、`insufficient`。文件名重叠只能产生 `inferred`。标成完成但没有代码或测试支撑的任务成为任务完整性缺口，不写成代码缺陷。无法追溯到需求的行为标成可能的擅自扩展，并要求人工审核。
- **Rationale**: 宪章禁止把文件重叠当成实现证据，也禁止把证据不足写成代码一定有错。
- **Alternatives considered**: 用向量相似度做全库匹配会扩大误报，并把推断伪装成直接证据。v0.1 宁可不下结论。

## Decision: 辅助审查使用显式配置的内网 OpenAI 兼容接口

- **Decision**: 只有配置了内部 `base_url` 且启用辅助审查时才调用模型。客户端使用带超时和有限重试的 HTTP 调用，只接受该配置主机。未配置时不发起网络请求，四个辅助维度标为 `SKIPPED`。失败、超时或返回无法解析时，该维度为 `ERROR`，已完成的确定性检查保留。送审上下文限制在变更相关片段和配置的字符上限内。密钥在送审前遮盖。源码中的指示不进入系统策略。
- **Rationale**: 宪章要求模型结论只是假设，且不能悄悄改送到外部服务。先交付无模型的静态模式，辅助审查是后加的一层。
- **Alternatives considered**: 绑定某一家云模型或编程助手会违反“不强制特定模型”的范围。在模型不可用时回退到公共接口会外发源码。

## Decision: 默认建议模式；严格结果可以计算，但不作为默认合并门禁

- **Decision**: 默认 `policy: advisory`。建议模式下发现只进入报告，进程不因发现而表示阻断。使用者明确选择 `strict` 时，只有配置点名的确定性失败才产生 `POLICY_BLOCKED`；纯模型假设不阻断。必需检查被跳过、出错或超时时，结果是 `REVIEW_INCOMPLETE`，不能算通过。v0.1 不提供持续集成里的合并阻断安装，也不在历史变更对照完成前把默认策略改成阻断。
- **Rationale**: 规格同时要求“明确配置的确定性失败可以给出阻断信号”和“对照完成前不启用阻止合并的质量门禁”。把信号做成显式选项、把默认和部署保持为建议，两条都能满足。
- **Alternatives considered**: v0.1 完全不实现严格策略，会让验收场景无法测试。把严格策略做成默认或自动接入合并，则违反宪章。

## Decision: 安装之后的使用步骤单独成文

- **Decision**: 安装说明停在「命令已经在 PATH 上」。安装之后怎么用，写在中文 `docs/usage.md`，按固定顺序展开，每一步都给出命令、成功时看到什么、失败时的退出码和下一步。顺序是：确认 `specguard version` 与 `specguard --help`；进入被审核 Java 仓库的 Git 根目录，不把 SpecGuard 源码克隆进去；确认 `openspec/changes/<变更名>/` 里有提案、设计和任务；在仓库根编写最小 `specguard.yaml`（`version: 1` 与可解析的 `git.base`）；运行 `specguard config validate --config specguard.yaml`；工作区有未提交改动时先提交，或显式加上 `--include-worktree`；运行 `specguard review --config specguard.yaml --mode static --policy advisory`；到标准输出打印的 `.specguard/reports/<变更名>-<提交前 12 位>.md` 与同名 `.json` 阅读报告，并链接 `docs/report-interpretation.md`；工程师自己决定是否接受变更，SpecGuard 不合并。多个进行中的变更必须加 `--change`。`--config` 在 v0.1 必须显式传入。严格模式 `--policy strict` 和内网辅助审查 `--mode assisted` 写在第一次使用之后，标明可选。`docs/install.md` 的「使用者」一节和两份 README 都链接 `docs/usage.md`。英文 README 只给链接，不另写长步骤。
- **Rationale**: 现在的安装文档只并列 `version`、`config validate` 和 `review` 三条命令，没有说明要站在哪个目录、配置至少写什么、未提交改动会停在哪里、报告文件在哪、退出码 0 仍可能有发现。空目录只证明命令已安装，继续在那里审核会因为「当前目录不在版本库中」而退出 4。把使用步骤和安装步骤分开，避免把验证用的空目录写成日常工作目录。
- **Alternatives considered**: 继续把三条命令留在 `docs/install.md`，读者仍然不知道失败后看什么。把 quickstart 的夹具场景当作使用者文档，会要求对方进入 SpecGuard 源码检出。第一次使用就写 `--mode assisted` 或 `--policy strict`，会把可选能力和默认建议模式混成必经步骤。另写一份英文长步骤会和现有中文安装文档分成两套，当前只在英文 README 里指向中文步骤。

## Decision: 用一份文档提供三档 specguard.yaml 模板

- **Decision**: 使用者复制的配置集中在中文 `docs/config-templates.md`，里面有三份完整且能通过配置模型校验的 YAML，标题分别为最小、标准、推荐。`docs/usage.md` 第 4 步链接该文档。命令不自动生成或加载这些文件，也不新增 `config init`。三档都写明 `version: 1`、可替换的 `git.base`、`review.mode: static`、`review.policy: advisory`、`review.llm_findings_block: false`、`llm.enabled: false`、`llm.external_fallback: false`。最小档不启用 `checks`。标准档启用并要求 `./mvnw -q -DskipTests package`（超时 600 秒）和 `./mvnw -q test`（超时 900 秒），并写明 `security.isolate_builds: true`。使用 Gradle 时，使用者只把这两条命令换成 `./gradlew assemble` 和 `./gradlew test`，同一份文件里不同时保留两套构建命令。推荐档包含标准档的构建和测试，再启用但不必需 `checkstyle`、`spotbugs`、`pmd`，命令分别是这三个程序名。工具不在 PATH 上时，这三项为 `SKIPPED`。JaCoCo 和 ArchUnit 不写入推荐档，因为 `jacoco` 和 `archunit` 不是允许的命令程序名，写入会使整份配置无效。严格模式和内网 `llm.base_url` 不出现在任一档的生效字段里。
- **Rationale**: 使用说明里的四行最小配置能够开始一次不跑构建的审核，但不能直接复制出带构建、测试和静态检查的文件。配置契约只有字段表。测试夹具里的 `specguard.yaml` 超时和检查开关是为测试服务的，复制到被审核仓库会得到错误的检查行为。三档分开后，第一次使用仍可以选最小档，需要构建证据时选标准档，本机有静态分析工具时选推荐档。推荐档把工具标成非必需，缺工具时不会把整次审核变成必需检查失败。
- **Alternatives considered**: 继续只在使用说明里放最小片段，读者仍要自己拼检查命令。做三个独立文件会让「一份模板」拆开，链接也更容易漏。把严格策略或辅助审查放进推荐档，会把可选能力写成默认文件，违反建议模式和禁止外部回退。为 JaCoCo 或 ArchUnit 编一条不在允许列表中的命令，配置校验会直接拒绝。新增 `specguard config init` 会扩大命令面，复制文档已经能完成同一件事。

## Decision: 不可信仓库的构建放进隔离工作区

- **Decision**: 默认文档说明 Maven 和 Gradle 会执行项目自己的插件。配置 `isolate_builds: true` 时，构建在仓库的临时副本中运行，不把构建写入原工作区。隔离失败时对应检查为 `ERROR`，不是 `PASS`。
- **Rationale**: 只读原则不能靠“相信每个被审核仓库的构建脚本”维持。隔离副本是比生产沙箱更简单、且足以覆盖 v0.1 的做法。
- **Alternatives considered**: 永远不运行构建最安全，但会失去测试和构建证据。在原工作区运行则可能改动被审核文件。容器沙箱更强，但依赖团队环境，不作为 v0.1 的必需条件。
