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

## Dependencies & Execution Order

### Phase Dependencies

- Setup（T001）→ Foundational（T002）→ 各用户故事 → Polish
- 所有测试任务都写在 tests/unit/test_install_entry.py，彼此不能并行

### User Story Dependencies

- **US1 (P1)**: 依赖 T002
- **US2 (P1)**: 依赖 US1。T009、T010 的插入位置在 T004、T005 的句子之后，T011 与 T006 改同一节
- **US3 (P2)**: 依赖 T002。改的是版本核对句，与 US1、US2 的段落不重叠，可以在 US1 之后任何时候做
- **US4 (P3)**: 依赖 T002。只改离线一节；与 US3 的 T014 改同一文件的不同段落，按顺序做

### Within Each User Story

- 测试先写并确认失败，再改文档，最后运行测试

### Parallel Opportunities

- T004、T005、T006 分别改三份文档，可以并行
- T009、T010 可以并行，T011 改 docs/install.md，单独做
- T014 与 T015 分别改 docs/install.md 和 docs/operations.md，可以并行
- T020 与 T021 可以并行

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

---

## Notes

- 只改文档和文档检查，不改运行代码与版本号
- 新增断言用完全匹配的原文，避免靠模糊匹配通过
- 不得删除或削弱现有断言
