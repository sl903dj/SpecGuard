# Research: 说明如何安装指定分支

所有结论来自 2026-10-28 的实际运行，环境为 `uv 0.13.5`。为了不动使用者已装的 SpecGuard，在线安装改用本地仓库的 `git+file://` 地址，并把 `UV_TOOL_DIR`、`UV_TOOL_BIN_DIR` 指到临时目录。uv 对 `git+file://` 和 `git+https://` 走同一套 Git 取源逻辑，只是传输方式不同。

## R1：不带分支的地址装哪个分支

- **Decision**：文档写明不带分支的地址安装 GitHub 默认分支 `master`。
- **Evidence**：`git ls-remote --symref origin HEAD` 返回 `ref: refs/heads/master`，提交是 `b5d0d06`。`origin/master:pyproject.toml` 的版本是 `0.1.0`，`origin/005-close-review-gaps` 的版本是 `0.4.0`。
- **Alternatives considered**：把默认分支改成功能分支，或把功能分支合并到 `master`。两者都超出规格范围，不采用。

## R2：带分支的地址能否装上指定分支

- **Decision**：文档使用 `uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"`。
- **Evidence**：`@master` 装上后 `specguard version` 输出 `0.1.0`；`@005-close-review-gaps` 装上后输出 `0.4.0`；含斜杠的分支 `@feat/slash` 也能装上。
- **Alternatives considered**：`#branch=` 等其他写法。`@<分支名>` 是用户要求的写法，也最短，不采用其他写法。

## R3：已安装时改装另一分支、或同一分支有新提交，是否会替换

- **Decision**：首次安装给出不带 `--force` 的命令。改装分支、装回 `master`、更新同一分支时，给出加 `--force` 的同一地址，并说明安装后用 `specguard version` 核对。
- **Evidence**：
  - 从 `master` 改装 `005-close-review-gaps`、再装回 `master`，不加 `--force` 也替换了，版本依次为 `0.1.0`、`0.4.0`、`0.1.0`。
  - 同一分支有新提交后，重新运行同一条命令，输出从 `0.4.0` 变为 `0.4.1`。
  - 加 `--force` 后同样拿到最新提交，输出 `0.4.2`。
  - `uv tool upgrade specguard` 只打印 `Nothing to upgrade`，版本不变。
- **Rationale**：当前 uv 不加 `--force` 也会替换，但文档无法保证使用者的 uv 版本与此相同。`--force` 在实测中同样有效，并且语义上明确要求重装，满足 FR-005 的“保证替换”。
- **Alternatives considered**：
  - 只写不带 `--force` 的命令。较旧的 uv 可能提示“已安装”而不替换，本次没有验证旧版本，不能保证。
  - 用 `uv tool upgrade`。实测不会取得分支上的新提交，文档明确不推荐。

## R4：分支名不存在时的表现

- **Decision**：文档写明分支名不存在时安装失败，已安装的版本保持不变，并给出查看远端分支名的方式。
- **Evidence**：`@no-such-branch` 报 `failed to fetch branch or tag`，之后 `specguard version` 仍输出原来的 `0.1.0`。
- **查看分支的方式**：网页 `https://github.com/sl903dj/SpecGuard/branches`，或命令 `git ls-remote --heads https://github.com/sl903dj/SpecGuard`。后者已实测能返回远端分支。

## R5：版本核对语句

- **Decision**：凡是写着“应输出某版本”的地方，都改为“与所装分支或检出的 `pyproject.toml` 版本一致”，并举例 `master` 为 `0.1.0`、`005-close-review-gaps` 为 `0.4.0`。
- **Evidence**：`docs/install.md` 第 28、70 行都写着“应输出 `0.4.0`”。`docs/operations.md` 第 27、102 行把 `0.4.0` 当作安装后的核对结果。`docs/usage.md` 第 16 行描述的是本版本命令的输出，不是安装预期，保持不变。
- **Alternatives considered**：只改 install.md。operations.md 第 102 行直接承接离线安装，留着会与 install.md 矛盾，所以一并修改。

## R6：离线安装选定分支

- **Decision**：外网准备改为 `git clone --branch <分支名> https://github.com/sl903dj/SpecGuard.git`，并说明不加 `--branch` 时取的是 `master`。随后的 `uv lock` 和 `uv export` 都在这个检出里执行，所以依赖跟随该分支。
- **Rationale**：保留现有测试要求的 `https://github.com/sl903dj/SpecGuard.git` 原文，只增加分支参数。
- **Alternatives considered**：克隆后再执行 `git checkout`。多一步，而且容易漏掉，不采用。

## R7：测试

- **Decision**：在 `tests/unit/test_install_entry.py` 中先新增失败的文档检查，再修改文档。检查内容：
  - 三份文档都含 `@<分支名>` 安装命令。
  - 三份文档都在不带分支的命令旁注明 `master`。
  - `docs/install.md` 含 `--force` 改装命令、查看分支的方式和 `git clone --branch`。
  - `docs/install.md` 不再出现“应输出 `0.4.0`”。
- **Baseline**：修改前全量测试为 `181 passed`。现有断言要求保留不带分支的命令原文和 `https://github.com/sl903dj/SpecGuard.git`，新方案都满足。
