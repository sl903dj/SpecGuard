# Feature Specification: 说明如何安装指定分支

**Feature Branch**: `006-branch-install-docs`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "安装命令默认安装 GitHub 默认分支 master；功能分支不合并到 master 时，文档需要说明如何用 uv tool install \"git+https://github.com/sl903dj/SpecGuard@<分支名>\" 安装指定分支，并在 README、README.en.md 和 docs/install.md 中写明"

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

### Edge Cases

- 分支名写错或远端没有该分支：文档说明安装会失败，应先核对远端分支名。
- 功能分支在安装后又有新提交：文档说明再次安装同一分支才能拿到新提交。
- 分支名含有斜杠：示例命令保持整段地址加引号，斜杠可以直接写在 `@` 后面。
- 功能分支被删除或已合并：文档说明这时改用默认安装。
- 内网电脑不能访问 GitHub：带分支的 Git 地址同样不可用，仍按离线一节处理。

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

### Key Entities

- **安装来源**: 使用者装 SpecGuard 时指定的位置。可以是默认分支、指定的功能分支，或本地源码检出。每种来源决定装到的版本。
- **分支名**: GitHub 远端上的分支名字，例如 `master`、`005-close-review-gaps`。它是带分支安装命令中 `@` 后面的部分。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 三份文档里，不带分支的安装命令共 3 处，每处都在相邻位置标明默认分支 `master`。
- **SC-002**: 三份文档里，每份至少有 1 处带 `@<分支名>` 的安装命令。
- **SC-003**: 新使用者只读 docs/install.md，能在 5 分钟内装上指定的功能分支，并用 `specguard version` 确认版本与该分支一致。
- **SC-004**: docs/install.md 里把功能分支版本写成默认安装预期结果的语句为 0 句。
- **SC-005**: 现有测试全部通过，新增的文档检查覆盖 SC-001 和 SC-002。

## Assumptions

- GitHub 默认分支保持为 `master`；本功能不改默认分支，也不把功能分支合并到 `master`。已核实远端默认分支是 `master`，版本为 0.1.0；`005-close-review-gaps` 的版本为 0.4.0。
- 只说明按分支安装；按标签或提交安装不在范围内。
- 使用者已有 `uv`，且能访问 GitHub；不能访问的情况仍走现有离线安装一节。
- docs/usage.md、docs/operations.md 等其他文档不在修改范围内，除非其中有把某版本写成默认安装结果的语句。
- 现有测试要求 docs/install.md 包含不带分支的安装命令，因此该命令保留。
