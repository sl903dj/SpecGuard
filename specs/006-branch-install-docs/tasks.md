---

description: "Task list for 006-branch-install-docs"
---

# Tasks: 说明如何安装指定分支

**Input**: Design documents from `specs/006-branch-install-docs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/install-docs.md, quickstart.md

**Tests**: 需要。宪章要求先有失败的测试；SC-005 和 research R7 要求文档检查。每个故事先在 `tests/unit/test_install_entry.py` 写检查，确认失败，再改文档。

**Organization**: 按用户故事分组。US1 和 US2 改同一批文档，按顺序做；US3、US4 改的段落不重叠。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可以并行（不同文件，不依赖未完成的任务）
- **[Story]**: 对应 spec.md 的用户故事

## 不可破坏的现有断言

修改文档时必须保留 `tests/unit/test_install_entry.py` 现有断言依赖的原文，包括：

- `uv tool install "git+https://github.com/sl903dj/SpecGuard"`，三份文档都要有
- `uv tool install --force`
- `https://github.com/sl903dj/SpecGuard.git`
- `id="offline-install"`
- 离线一节的各条命令
- 以 `## 内网离线安装` 切分文本后，前后两段各自的空目录说明，且说明位于 `mkdir -p /tmp/specguard-install-check` 之前

---

## Phase 1: Setup

- [X] T001 运行 `.venv/bin/python -m pytest -q` 记录基线，预期 `181 passed`，结果写入 specs/006-branch-install-docs/quickstart.md 末尾的“验证记录”

---

## Phase 2: Foundational

- [X] T002 在 tests/unit/test_install_entry.py 顶部新增常量：
  - `DEFAULT_INSTALL = 'uv tool install "git+https://github.com/sl903dj/SpecGuard"'`
  - `BRANCH_INSTALL_ZH = 'uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"'`
  - `BRANCH_INSTALL_EN = 'uv tool install "git+https://github.com/sl903dj/SpecGuard@<branch>"'`

  再新增辅助函数 `_section(text, heading)`，返回从 `heading` 到下一个同级 `## ` 标题之间的文本。只加常量和辅助函数，不改现有测试。

**Checkpoint**: 运行 `.venv/bin/python -m pytest -q tests/unit/test_install_entry.py`，仍全部通过

---

## Phase 3: User Story 1 - 知道默认安装装的是哪个分支 (Priority: P1) 🎯 MVP

**Goal**: 三份文档在不带分支的命令旁写明它安装默认分支 `master`，未合并的功能分支不在其中（FR-001、FR-002；契约 C1、C3、C4）

**Independent Test**: 只读三份文档的安装一节，能回答“这条命令装 `master`”

### Tests for User Story 1

- [X] T003 [US1] 在 tests/unit/test_install_entry.py 新增 `test_default_install_names_master_branch`：
  - README.md 的 `_section(text, "## 安装")` 和 docs/install.md 的 `_section(text, "## 使用者")`：含 `DEFAULT_INSTALL`、`默认分支`、`` `master` ``、`未合并`
  - README.en.md 的 `_section(text, "## Install")`：含 `DEFAULT_INSTALL`、`default branch`、`` `master` ``、`not merged`

  运行后确认该测试失败。

### Implementation for User Story 1

- [X] T004 [P] [US1] 在 README.md “## 安装”的第一个命令块后加一句：这条命令安装 GitHub 默认分支 `master`；未合并到 `master` 的功能分支不在其中。命令原文不变。
- [X] T005 [P] [US1] 在 README.en.md “## Install”的第一个命令块后加入与 T004 含义相同的英文句子，须含 `default branch`、`` `master` ``、`not merged`。
- [X] T006 [P] [US1] 在 docs/install.md “## 使用者”的命令块后加入与 T004 相同含义的说明。
- [X] T007 [US1] 运行 `.venv/bin/python -m pytest -q tests/unit/test_install_entry.py`，T003 与现有测试全部通过

**Checkpoint**: US1 可单独交付

---

## Phase 4: User Story 2 - 安装尚未合并的功能分支 (Priority: P1)

**Goal**: 三份文档给出 `@<分支名>` 安装命令；docs/install.md 说明真实示例、改装、更新、装回 `master`、查看分支、失败表现和无法访问 GitHub 的情况（FR-003 到 FR-006；契约 C2、C5 到 C9、C12）

**Independent Test**: 只按 docs/install.md 装上 `005-close-review-gaps`，`specguard version` 输出 `0.4.0`

### Tests for User Story 2

- [X] T008 [US2] 在 tests/unit/test_install_entry.py 新增 `test_docs_explain_branch_install`：
  - README.md 和 docs/install.md 含 `BRANCH_INSTALL_ZH`；README.en.md 含 `BRANCH_INSTALL_EN`
  - docs/install.md 的 `_section(text, "## 使用者")` 含：
    - `uv tool install "git+https://github.com/sl903dj/SpecGuard@005-close-review-gaps"`
    - `uv tool install --force "git+https://github.com/sl903dj/SpecGuard@<分支名>"`
    - `uv tool install --force "git+https://github.com/sl903dj/SpecGuard"`
    - `uv tool upgrade`
    - `git ls-remote --heads https://github.com/sl903dj/SpecGuard`
    - `https://github.com/sl903dj/SpecGuard/branches`
    - `安装失败`
    - `离线安装`

  运行后确认该测试失败。

### Implementation for User Story 2

- [X] T009 [P] [US2] 在 README.md “## 安装”中 T004 的句子之后加一个命令块，内容为 `uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"`。说明 `<分支名>` 换成远端分支名，并链接到 docs/install.md 的“安装指定分支”子节，链接为 `docs/install.md#branch-install`。
- [X] T010 [P] [US2] 在 README.en.md 做与 T009 对应的修改：命令用 `@<branch>`，链接同为 `docs/install.md#branch-install`。
- [X] T011 [US2] 在 docs/install.md “## 使用者”末尾、“## 验证本地源码”之前，新增 `### 安装指定分支` 和锚点 `<a id="branch-install"></a>`。依次写入以下内容，依据见 research R2 到 R4：
  1. 命令形式 `uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"`，整段地址加引号，分支名可含斜杠。
  2. 示例 `uv tool install "git+https://github.com/sl903dj/SpecGuard@005-close-review-gaps"`，装后 `specguard version` 输出 `0.4.0`。
  3. 已装时改装另一分支，或同一分支有新提交时更新，都用 `uv tool install --force "git+https://github.com/sl903dj/SpecGuard@<分支名>"`。
  4. 装回 `master` 用 `uv tool install --force "git+https://github.com/sl903dj/SpecGuard"`。
  5. `uv tool upgrade` 不会取得分支上的新提交，不用它更新分支安装。
  6. 查看分支名可用 `git ls-remote --heads https://github.com/sl903dj/SpecGuard`，或打开 `https://github.com/sl903dj/SpecGuard/branches`。
  7. 分支名不存在时安装失败，已装版本不变。
  8. 分支已删除或已合并时改用默认安装。
  9. 不能访问 GitHub 时带分支的地址同样不可用，改走 [内网离线安装](#offline-install)。
- [X] T012 [US2] 运行 `.venv/bin/python -m pytest -q tests/unit/test_install_entry.py`，全部通过

**Checkpoint**: US1、US2 均可独立验证

---

## Phase 5: User Story 3 - 确认装到的版本 (Priority: P2)

**Goal**: 版本核对语句对应安装来源，不再把 `0.4.0` 写成固定预期（FR-007；契约 C10、C13）

**Independent Test**: docs/install.md、docs/operations.md 中每处版本核对都对应一种安装来源

### Tests for User Story 3

- [X] T013 [US3] 在 tests/unit/test_install_entry.py 新增 `test_version_check_follows_installed_branch`：
  - docs/install.md 不含 ``应输出 `0.4.0` ``，含 `与所装分支` 和 `` `0.1.0` ``
  - docs/operations.md 不含 ``得到 `0.4.0` `` 和 ``确认输出 `0.4.0` ``，含 `与所装分支`

  运行后确认该测试失败。

### Implementation for User Story 3

- [X] T014 [P] [US3] 改 docs/install.md 的两处版本核对，分别在“验证本地源码”和离线一节，原句为 ``specguard version` 应输出 `0.4.0`。`` 改为：输出与所装分支或检出的 `pyproject.toml` 版本一致，例如 `master` 为 `0.1.0`、`005-close-review-gaps` 为 `0.4.0`。保留同句前面的 `src/specguard` 说明。
- [X] T015 [P] [US3] 改 docs/operations.md 第 27 行 ``1. `specguard version` 得到 `0.4.0`。`` 和第 102 行 ``确认输出 `0.4.0` ``，都改为“与所装分支一致”。第 27 行补一句：本文档描述的命令以 `0.4.0` 为准。
- [X] T016 [US3] 运行 `.venv/bin/python -m pytest -q tests/unit/test_install_entry.py`，全部通过

**Checkpoint**: US3 可独立验证

---

## Phase 6: User Story 4 - 内网离线安装指定分支 (Priority: P3)

**Goal**: 离线一节在外网准备阶段选定分支（FR-008；契约 C11）

**Independent Test**: 只读离线一节，能找到选定分支的步骤

### Tests for User Story 4

- [X] T017 [US4] 在 tests/unit/test_install_entry.py 新增 `test_offline_install_selects_branch`。在 `text.split("## 内网离线安装", 1)[1]` 中检查以下三项，运行后确认失败：
  - `git clone --branch <分支名> https://github.com/sl903dj/SpecGuard.git`
  - ``不加 `--branch` ``
  - `` `master` ``

### Implementation for User Story 4

- [X] T018 [US4] 改 docs/install.md 离线一节“外网准备”的命令块：
  - 把 `git clone https://github.com/sl903dj/SpecGuard.git` 改为 `git clone --branch <分支名> https://github.com/sl903dj/SpecGuard.git`，`cd SpecGuard` 和其余命令不变。
  - 在命令块前说明：不加 `--branch` 时取 `master`；随后的 `uv lock` 和 `uv export` 在该检出中执行，依赖跟随该分支。
- [X] T019 [US4] 运行 `.venv/bin/python -m pytest -q tests/unit/test_install_entry.py`，全部通过

**Checkpoint**: 全部故事完成

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T020 [P] 对照 README.md 与 README.en.md 的“安装/Install”一节，逐句确认含义一一对应，没有多出或缺少的说明（FR-009）
- [X] T021 确认 `git diff --stat` 只涉及以下文件，不改 `src/` 和 `pyproject.toml`（FR-010）：README.md、README.en.md、docs/install.md、docs/operations.md、tests/unit/test_install_entry.py、specs/006-branch-install-docs/
- [X] T022 运行全量 `.venv/bin/python -m pytest -q`，预期 `181 + 新增测试数` 全部通过
- [X] T023 按 specs/006-branch-install-docs/quickstart.md 第 2 节，在隔离的 `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` 中实际安装：
  - 预期依次为 `master` 输出 `0.1.0`、`@005-close-review-gaps` 输出 `0.4.0`、装回 `master` 输出 `0.1.0`、不存在的分支安装失败且版本不变。
  - 不能访问 GitHub 时改用 `git+file://` 本地检出。
  - 结束后清理临时目录。
- [X] T024 把 T001、T022、T023 的结果写入 specs/006-branch-install-docs/quickstart.md 末尾的“验证记录”

---

## Phase 8: User Story 5 - 卸载 SpecGuard (Priority: P2)

**Goal**: 三份文档给出卸载命令。docs/install.md 末尾新增“## 卸载”一节，覆盖契约 C14 到 C20，对应 FR-011 到 FR-016：

- 卸载适用于所有安装来源；
- 卸载后如何确认；
- 被审核仓库的配置和报告保留；
- 可选的缓存清理；
- 重复卸载的提示；
- 离线安装的残留目录；
- 换分支不需要先卸载；
- `.venv` 不受影响。

**Independent Test**: 只按 docs/install.md 的卸载一节操作，`command -v specguard` 无输出；被审核仓库里 `specguard.yaml` 和 `.specguard/reports/` 的文件指纹不变（quickstart 第 3 节）

**前提**：T001 到 T024 已完成，当前全量基线为 `185 passed`。`_section`、`DEFAULT_INSTALL` 等辅助代码已在 T002 中加好，直接复用。

### Tests for User Story 5

- [X] T025 [US5] 在 tests/unit/test_install_entry.py 新增 `test_docs_explain_uninstall`。运行后确认该测试失败。检查内容如下：
  - README.md、README.en.md、docs/install.md 都含 `uv tool uninstall specguard`；README.md 和 README.en.md 都含 `docs/install.md#uninstall`（C14）
  - docs/install.md 含 `<a id="uninstall"></a>`，且 `text.index("## 卸载")` 大于 `text.index("## 开发者")`（C15）
  - 取 `uninstall = _section(text, "## 卸载")`，其中依次含以下内容：
    - `默认分支`、`指定分支`、`本地检出`、`离线安装`、`command -v specguard`、`hash -r`（C16）
    - `specguard.yaml`、`.specguard/reports/`、`calibration.json`、`保留`、`手工删除`（C17）
    - `uv cache clean specguard`、`可选`（C18）
    - `` `specguard` is not installed ``、`不需要联网`、`/tmp/specguard-wheels`（C19）
    - `不需要先卸载`、`.venv`（C20）
  - `uninstall` 中不含 `rm `，确保不给出删除被审核仓库文件的命令（research R9）

### Implementation for User Story 5

- [X] T026 [P] [US5] 在 README.md “## 安装”中、“安装和运行的其余步骤见”一段之前，加入卸载说明：
  - 一句“卸载：”；
  - 命令块 `uv tool uninstall specguard`；
  - 一句“卸载不会删除被审核仓库里的配置和报告，详见 [卸载](docs/install.md#uninstall)。”
- [X] T027 [P] [US5] 在 README.en.md “## Install” 的对应位置，即 “Further install and run steps are in” 一段之前，加入与 T026 含义相同的英文说明：
  - 命令块 `uv tool uninstall specguard`；
  - 说明卸载不删除被审核仓库的配置和报告；
  - 链接 `docs/install.md#uninstall`。
- [X] T028 [US5] 在 docs/install.md 文件末尾、“## 开发者”一节之后，新增 `## 卸载` 和 `<a id="uninstall"></a>`。依次写入以下内容，依据见 research R8 到 R11 和 data-model“卸载范围”：
  1. 命令块 `uv tool uninstall specguard`。写明它适用于默认分支、指定分支、本地检出和离线安装的 SpecGuard，按工具名删除命令和工具环境。
  2. 确认方法：运行 `command -v specguard`，没有输出即已卸载。在原终端里如果报 `No such file or directory`，先执行 `hash -r`，或新开一个终端。
  3. 被审核仓库里的 `specguard.yaml` 和 `.specguard/reports/`（含 `calibration.json`）都保留。卸载不修改被审核仓库，需要时由使用者手工删除。不要写删除命令。
  4. 可选：`uv cache clean specguard` 只清除 SpecGuard 的下载缓存，用于释放磁盘空间，不是卸载的必需步骤。
  5. 已卸载后再运行卸载，会提示 `` `specguard` is not installed ``，这不是故障。
  6. 离线安装的卸载用同一条命令，不需要联网。传入内网的源码目录和 `/tmp/specguard-wheels` 需要另外手工删除。
  7. 换分支不需要先卸载，见 [安装指定分支](#branch-install)。开发者检出里的 `.venv` 不受卸载命令影响，需要时删除该检出里的 `.venv`。

  注意：该节文字不得包含 `mkdir -p /tmp/specguard-install-check`，也不得包含“空目录是当前工作目录，不是安装位置”，以免影响 `test_empty_directory_is_only_for_version_check` 对离线段的定位。
- [X] T029 [US5] 运行 `.venv/bin/python -m pytest -q tests/unit/test_install_entry.py`，T025 与现有测试全部通过

**Checkpoint**: US5 可独立验证

---

## Phase 9: Polish（卸载部分）

- [X] T030 [P] 对照 README.md 与 README.en.md 的卸载说明，逐句确认含义一致（FR-009）
- [X] T031 [P] 确认 `git diff --stat` 只涉及 README.md、README.en.md、docs/install.md、tests/unit/test_install_entry.py 和 specs/006-branch-install-docs/，不改 `src/` 和 `pyproject.toml`（FR-010）
- [X] T032 运行全量 `.venv/bin/python -m pytest -q`，预期 `186 passed`
- [X] T033 按 specs/006-branch-install-docs/quickstart.md 第 3 节，在隔离的 `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` 中照新文档卸载：
  - 预期卸载退出码 `0`，`bin` 目录为空；
  - 重复卸载退出码 `2`，提示 `` `specguard` is not installed ``；
  - 模拟被审核仓库的文件指纹无差异；
  - 结束后清理临时目录。
  - 不动 `~/.local/bin` 下使用者的真实安装。
- [X] T034 把 T032、T033 的结果追加到 specs/006-branch-install-docs/quickstart.md 末尾的“验证记录”

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup（T001）→ Foundational（T002）→ 各用户故事 → Polish
- 所有测试任务都写在 tests/unit/test_install_entry.py，彼此不能并行

### User Story Dependencies

- **US1 (P1)**: 依赖 T002
- **US2 (P1)**: 依赖 US1。T009、T010 的插入位置在 T004、T005 的句子之后，T011 与 T006 改同一节
- **US3 (P2)**: 依赖 T002。改的是版本核对句，与 US1、US2 的段落不重叠，可以在 US1 之后任何时候做
- **US4 (P3)**: 依赖 T002。只改离线一节；与 US3 的 T014 改同一文件的不同段落，按顺序做
- **US5 (P2)**：
  - 依赖 T002 中的 `_section` 辅助函数，该函数已完成。
  - T026、T027 依赖 US2 已加入 README 的段落，用来确定插入位置，这部分也已完成。
  - T028 只在 docs/install.md 末尾追加，与前面各节不重叠。
  - US5 不依赖未完成的任务，可以立即开始。

### Within Each User Story

- 测试先写并确认失败，再改文档，最后运行测试

### Parallel Opportunities

- T004、T005、T006 分别改三份文档，可以并行
- T009、T010 可以并行，T011 改 docs/install.md，单独做
- T014 与 T015 分别改 docs/install.md 和 docs/operations.md，可以并行
- T020 与 T021 可以并行
- T025 确认失败后，T026、T027 分别改两份 README，可以并行；T028 改 docs/install.md，单独做
- T030 与 T031 可以并行
- 同一文件的多处修改必须逐处顺序进行，不要并行提交

---

## Parallel Example: User Story 1

```bash
# T003 确认失败后，三份文档同时改：
Task: "T004 README.md 安装一节加默认分支说明"
Task: "T005 README.en.md Install 一节加 default branch 说明"
Task: "T006 docs/install.md 使用者一节加默认分支说明"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 T001、T002
2. 完成 US1（T003 到 T007）
3. 停下验证：三份文档都说明默认分支是 `master`

### Incremental Delivery

1. US1：说明默认分支
2. US2：使用者可以安装功能分支，这是本功能的主要价值
3. US3：版本核对不再误导
4. US4：离线也能选定分支
5. Polish：全量测试，并照文档实际安装验证
6. US5：卸载说明（T025 到 T029），然后做 Phase 9 的复核与实测（T030 到 T034）。T001 到 T024 已完成，这一步是当前要做的增量。

---

## Notes

- 只改文档和文档检查，不改运行代码与版本号
- 新增断言用完全匹配的原文，避免靠模糊匹配通过
- 不得删除或削弱现有断言

## Phase 10: Convergence

- [X] T035 在 specs/006-branch-install-docs/quickstart.md 第 2、3 节的隔离环境变量中加入 `UV_CACHE_DIR=/tmp/sg-check/cache`，使 `uv cache clean specguard` 只清除隔离缓存；并在两节的清理步骤中一并 `unset UV_CACHE_DIR`、删除该目录，让“隔离目录，不影响已装版本”的说法与实际一致 per plan: quickstart 验证指南 / T033 (partial)
