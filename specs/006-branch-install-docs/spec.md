# Feature Specification: 说明如何安装指定分支和卸载

**Feature Branch**: `006-branch-install-docs`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "安装命令默认安装 GitHub 默认分支 master；功能分支不合并到 master 时，文档需要说明如何用 uv tool install \"git+https://github.com/sl903dj/SpecGuard@<分支名>\" 安装指定分支，并在 README、README.en.md 和 docs/install.md 中写明"

**Update (2026-10-28)**: User description: "项目还没有卸载指令，在 006 分支完善"。新增 User Story 5 和 FR-011 到 FR-016。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 知道默认安装装的是哪个分支 (Priority: P1)

使用者照着 README 或安装文档复制不带分支的安装命令。文档在这条命令旁边写明：它安装 GitHub 默认分支 `master`，装到的是 `master` 上的版本，不包含尚未合并到 `master` 的功能分支。

**Why this priority**: 现在 `master` 是 0.1.0，功能分支已到 0.4.0，安装文档却写着 `specguard version` 应输出 `0.4.0`。使用者照做会装到旧版本，并误以为安装失败或功能缺失。这是最直接的误导。

**Independent Test**: 只读 README.md、README.en.md、docs/install.md 中不带分支的安装命令及其相邻说明，能回答“这条命令装哪个分支”，答案是 `master`。

**Acceptance Scenarios**:

1. **Given** 使用者打开 README.md，**When** 读到不带分支的安装命令，**Then** 相邻文字写明它安装默认分支 `master`。
2. **Given** 使用者打开 README.en.md，**When** 读到同一条命令，**Then** 相邻英文说明写明它安装默认分支 `master`。
3. **Given** 使用者打开 docs/install.md 的“使用者”一节，**When** 读到同一条命令，**Then** 说明写明它安装 `master`，且未合并的功能分支不在其中。

---

### User Story 2 - 安装尚未合并的功能分支 (Priority: P1)

使用者需要某个尚未合并到 `master` 的功能分支，例如 `005-close-review-gaps`。三份文档都给出 `uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"` 这一形式，说明 `<分支名>` 换成远端分支的名字，并给出一个用真实分支名替换后的示例。

**Why this priority**: 功能分支不合并到 `master` 时，这是使用者拿到新功能的唯一在线途径。缺少这条说明，0.2 到 0.4 的功能对使用者不可见。

**Independent Test**: 只按 docs/install.md 的说明，把 `<分支名>` 换成一个存在的远端分支并安装，再离开源码目录运行 `specguard version`，输出与该分支声明的版本一致。

**Acceptance Scenarios**:

1. **Given** 使用者要装分支 `005-close-review-gaps`，**When** 按文档把 `<分支名>` 替换后运行安装命令，**Then** `specguard version` 输出该分支的版本 `0.4.0`。
2. **Given** 使用者已经从 `master` 装过 SpecGuard，**When** 按文档改装某个功能分支，**Then** 文档给出的命令能让新分支替换已安装的版本，而不是因“已安装”而保留旧版本。
3. **Given** 使用者想从功能分支回到默认分支，**When** 按文档操作，**Then** 能重新装回 `master`。
4. **Given** 使用者不知道有哪些分支，**When** 阅读安装文档，**Then** 文档告诉他到哪里查看远端分支名。

---

### User Story 3 - 确认装到的版本 (Priority: P2)

安装后，使用者运行 `specguard version`，并对照文档判断自己装到的是不是想要的分支。文档不再把某个固定版本号写成所有安装方式的预期输出，而是说明版本取决于安装的分支。

**Why this priority**: 版本核对是使用者发现“装错分支”的唯一手段。写死的版本号会让默认安装看起来像失败。

**Independent Test**: 阅读 docs/install.md 中所有“应输出”版本号的语句，每一句都能对应到一种明确的安装来源，没有一句把功能分支的版本说成默认安装的结果。

**Acceptance Scenarios**:

1. **Given** 使用者用不带分支的命令安装，**When** 对照文档核对版本，**Then** 文档没有要求他看到 `0.4.0`。
2. **Given** 使用者从本地源码检出安装，**When** 对照文档核对版本，**Then** 文档说明版本与该检出所在分支的版本一致。

---

### User Story 4 - 内网离线安装指定分支 (Priority: P3)

内网使用者按离线安装一节在外网电脑上取源码。文档说明取源码时如何选定功能分支，使传入内网的源码就是想要的分支。

**Why this priority**: 离线一节同样从默认分支取源码，问题相同，但受影响的人较少。

**Independent Test**: 只读离线安装一节，能找到在外网准备阶段选定分支的步骤。

**Acceptance Scenarios**:

1. **Given** 内网使用者需要功能分支，**When** 按离线一节的外网准备步骤取源码，**Then** 步骤里有选定分支的方式，且后续的依赖导出和安装都基于该分支。

---

### User Story 5 - 卸载 SpecGuard (Priority: P2)

使用者不再需要 SpecGuard，或者想清理后重新安装。三份文档都给出卸载命令，说明卸载后如何确认命令已经不存在。docs/install.md 还说明卸载不会动哪些东西：被审核仓库里的配置和报告都保留，由使用者自己决定是否删除。

**Why this priority**: 现在文档只讲安装，没有讲卸载。使用者只能自己猜要删哪些目录，可能误删被审核仓库里的报告，也可能留下不再需要的缓存。卸载不影响拿到新功能，所以排在两个 P1 故事之后。

**Independent Test**: 只按 docs/install.md 的卸载说明操作，运行 `specguard version` 时提示命令不存在；被审核仓库里的 `specguard.yaml` 和 `.specguard/reports/` 保持不变。

**Acceptance Scenarios**:

1. **Given** 使用者用任一种方式装过 SpecGuard（默认分支、指定分支、本地检出或离线安装），**When** 运行文档给出的卸载命令，**Then** `specguard` 命令不再可用。
2. **Given** 使用者已经卸载，**When** 再次运行卸载命令，**Then** 文档说明会提示“未安装”，这不是故障。
3. **Given** 被审核仓库里有 `specguard.yaml` 和 `.specguard/reports/`，**When** 使用者卸载 SpecGuard，**Then** 文档写明这些文件不受影响，需要时由使用者手工删除。
4. **Given** 使用者想释放磁盘空间，**When** 阅读卸载说明，**Then** 文档给出清除 SpecGuard 下载缓存的命令，并说明这一步可选。
5. **Given** 内网离线安装过的使用者，**When** 卸载，**Then** 文档说明卸载命令不需要联网，传入内网的源码目录和轮子目录要另外手工删除。
6. **Given** 使用者只想换一个分支，**When** 阅读卸载说明，**Then** 文档说明换分支不需要先卸载。

---

### Edge Cases

- 分支名写错或远端没有该分支：文档说明安装会失败，应先核对远端分支名。
- 功能分支在安装后又有新提交：文档说明再次安装同一分支才能拿到新提交。
- 分支名含有斜杠：示例命令保持整段地址加引号，斜杠可以直接写在 `@` 后面。
- 功能分支被删除或已合并：文档说明这时改用默认安装。
- 内网电脑不能访问 GitHub：带分支的 Git 地址同样不可用，仍按离线一节处理。
- 未安装就运行卸载：提示未安装并以非零状态结束，不影响其他工具。
- 卸载后命令仍能找到：说明当前终端可能还缓存着旧的命令路径，或另有一份不是用 `uv tool` 安装的 SpecGuard，例如开发者检出里的虚拟环境。
- 开发者检出里的虚拟环境：卸载命令不会删除它，需要时删除检出里的 `.venv`。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: README.md、README.en.md、docs/install.md 必须保留现有不带分支的安装命令 `uv tool install "git+https://github.com/sl903dj/SpecGuard"`，原文不变。
- **FR-002**: 三份文档必须在该命令相邻处写明它安装 GitHub 默认分支 `master`，未合并到 `master` 的功能分支不在其中。
- **FR-003**: 三份文档必须给出安装指定分支的命令形式 `uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"`，并说明 `<分支名>` 是远端分支的名字。
- **FR-004**: docs/install.md 必须给出至少一个把 `<分支名>` 替换成真实分支名的完整示例。
- **FR-005**: docs/install.md 必须说明已安装 SpecGuard 时如何改装另一个分支，以及如何装回 `master`，并保证所给命令会替换已安装的版本。
- **FR-006**: docs/install.md 必须说明在哪里查看可安装的远端分支名，以及分支名不存在时安装会失败。
- **FR-007**: docs/install.md 中每一句“`specguard version` 应输出某版本”的说明必须对应明确的安装来源；默认安装不得被描述为输出功能分支的版本。
- **FR-008**: docs/install.md 的离线安装一节必须说明在外网准备阶段如何选定分支。
- **FR-009**: README.en.md 的说明必须与 README.md 含义一致，不多也不少。
- **FR-010**: 本功能只改文档和检查文档的测试，不改变 SpecGuard 的运行行为、命令或版本号。
- **FR-011**: README.md、README.en.md、docs/install.md 必须给出卸载命令 `uv tool uninstall specguard`。
- **FR-012**: docs/install.md 必须说明卸载适用于所有安装来源（默认分支、指定分支、本地检出、离线安装），并说明如何确认卸载后命令已不可用。
- **FR-013**: docs/install.md 必须写明卸载不修改被审核仓库，`specguard.yaml` 和报告目录 `.specguard/reports/`（含 `calibration.json`）都保留，需要时由使用者手工删除。
- **FR-014**: docs/install.md 必须给出可选的缓存清理命令 `uv cache clean specguard`，并说明它只清除下载缓存，不是卸载的必需步骤。
- **FR-015**: docs/install.md 必须说明重复卸载会提示未安装；离线安装的卸载不需要联网，传入内网的源码目录和轮子目录需要另外手工删除。
- **FR-016**: docs/install.md 必须说明换分支不需要先卸载，并说明开发者检出里的 `.venv` 不受卸载命令影响。

### Key Entities

- **安装来源**: 使用者装 SpecGuard 时指定的位置。可以是默认分支、指定的功能分支，或本地源码检出。每种来源决定装到的版本。
- **分支名**: GitHub 远端上的分支名字，例如 `master`、`005-close-review-gaps`。它是带分支安装命令中 `@` 后面的部分。
- **卸载范围**: 卸载命令删除的是 SpecGuard 命令及其工具环境。不在卸载范围内、需要手工处理的有：被审核仓库里的配置和报告、下载缓存、离线传入的源码和轮子目录，以及开发者检出里的虚拟环境。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 三份文档里，不带分支的安装命令共 3 处，每处都在相邻位置标明默认分支 `master`。
- **SC-002**: 三份文档里，每份至少有 1 处带 `@<分支名>` 的安装命令。
- **SC-003**: 新使用者只读 docs/install.md，能在 5 分钟内装上指定的功能分支，并用 `specguard version` 确认版本与该分支一致。
- **SC-004**: docs/install.md 里把功能分支版本写成默认安装预期结果的语句为 0 句。
- **SC-005**: 现有测试全部通过，新增的文档检查覆盖 SC-001 和 SC-002。
- **SC-006**: 三份文档里，每份至少有 1 处卸载命令。
- **SC-007**: 使用者只按 docs/install.md 卸载后，`specguard` 命令不可用，被审核仓库中的配置和报告文件数量不变。

## Assumptions

- GitHub 默认分支保持为 `master`；本功能不改默认分支，也不把功能分支合并到 `master`。已核实远端默认分支是 `master`，版本为 0.1.0；`005-close-review-gaps` 的版本为 0.4.0。
- 只说明按分支安装；按标签或提交安装不在范围内。
- 使用者已有 `uv`，且能访问 GitHub；不能访问的情况仍走现有离线安装一节。
- docs/usage.md、docs/operations.md 等其他文档不在修改范围内，除非其中有把某版本写成默认安装结果的语句。
- 现有测试要求 docs/install.md 包含不带分支的安装命令，因此该命令保留。
- 卸载只覆盖用 `uv tool` 安装的 SpecGuard；SpecGuard 不在用户主目录写配置或状态，代码中没有读写主目录的位置，因此卸载不需要清理用户级配置。
- 卸载行为已在隔离目录中实测（uv 0.13.5）：
  - `uv tool uninstall specguard` 删除命令和工具环境，退出码 `0`。
  - 再次运行会提示 `` `specguard` is not installed ``，退出码 `2`。
  - `uv cache clean specguard` 只清除下载缓存，退出码 `0`。
- 持续集成里的临时环境不需要卸载步骤，不在范围内。
