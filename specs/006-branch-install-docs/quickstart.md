# Quickstart: 验证分支安装文档

## 前提

- 在 SpecGuard 检出根目录，分支 `006-branch-install-docs`，已有 `.venv`。
- 已安装 `uv`。在线验证需要能访问 GitHub。

## 1. 文档检查

```bash
.venv/bin/python -m pytest -q tests/unit/test_install_entry.py
.venv/bin/python -m pytest -q
```

预期：全部通过。修改前的基线是 `181 passed`，新增检查见 [contracts/install-docs.md](contracts/install-docs.md)。

## 2. 照文档实际安装（隔离目录，不影响已装版本）

```bash
export UV_TOOL_DIR=/tmp/sg-check/tools UV_TOOL_BIN_DIR=/tmp/sg-check/bin UV_CACHE_DIR=/tmp/sg-check/cache
uv tool install "git+https://github.com/sl903dj/SpecGuard"
/tmp/sg-check/bin/specguard version          # 预期 0.1.0（master）
uv tool install --force "git+https://github.com/sl903dj/SpecGuard@005-close-review-gaps"
/tmp/sg-check/bin/specguard version          # 预期 0.4.0
uv tool install --force "git+https://github.com/sl903dj/SpecGuard"
/tmp/sg-check/bin/specguard version          # 预期 0.1.0
uv tool install --force "git+https://github.com/sl903dj/SpecGuard@no-such-branch"   # 预期失败
/tmp/sg-check/bin/specguard version          # 预期仍是 0.1.0
git ls-remote --heads https://github.com/sl903dj/SpecGuard   # 列出可安装的分支
unset UV_TOOL_DIR UV_TOOL_BIN_DIR UV_CACHE_DIR
rm -rf /tmp/sg-check
```

不能访问 GitHub 时，可以把地址换成 `git+file://<本地检出>`，用同样的步骤验证，分支名用本地已有的分支。

## 3. 照文档卸载（隔离目录，不影响已装版本）

用 `export UV_TOOL_DIR=/tmp/sg-check/tools UV_TOOL_BIN_DIR=/tmp/sg-check/bin UV_CACHE_DIR=/tmp/sg-check/cache` 隔离安装一份，然后执行下面的步骤。三个变量都要设：不设 `UV_CACHE_DIR` 时，`uv cache clean specguard` 会清除使用者本机的 uv 缓存。

先建一个模拟的被审核仓库，并记下文件指纹：

```bash
mkdir -p /tmp/sg-reviewed/.specguard/reports
echo "version: 1" > /tmp/sg-reviewed/specguard.yaml
echo '{"complete": false}' > /tmp/sg-reviewed/.specguard/reports/calibration.json
(cd /tmp/sg-reviewed && find . -type f | sort | xargs sha256sum) > /tmp/sg-before.txt
```

卸载并检查：

```bash
uv tool uninstall specguard               # 预期 Uninstalled 1 executable，退出码 0
ls /tmp/sg-check/bin                      # 预期为空
uv tool uninstall specguard               # 预期 `specguard` is not installed，退出码 2
(cd /tmp/sg-reviewed && find . -type f | sort | xargs sha256sum) | diff - /tmp/sg-before.txt   # 预期无差异
uv cache clean specguard                  # 可选，预期退出码 0
```

清理：

```bash
unset UV_TOOL_DIR UV_TOOL_BIN_DIR UV_CACHE_DIR
rm -rf /tmp/sg-check /tmp/sg-reviewed /tmp/sg-before.txt
```

在真实安装上验证时，不设 `UV_TOOL_DIR`，卸载后执行 `hash -r` 再运行 `command -v specguard`，预期没有输出。验证完按 docs/install.md 的安装命令装回。

## 4. 人工通读

- README.md 和 README.en.md 安装一节的条目一一对应，包括卸载命令。
- docs/install.md 和 docs/operations.md 里每处版本核对都对应一种安装来源。
- docs/install.md 的卸载一节没有给出删除被审核仓库文件的命令。

## 验证记录（2026-10-28，uv 0.13.5）

- 修改前全量测试：`181 passed`。
- 修改后：`tests/unit/test_install_entry.py` 为 `12 passed`，全量 `185 passed`。新增 4 条检查，每条都先确认失败再改文档。
- 第 2 节在隔离目录中从 GitHub 实际安装，结果如下，与文档一致：
  - 不带分支：`specguard==0.1.0`，来自 `b5d0d06`，`specguard version` 输出 `0.1.0`。
  - `--force …@005-close-review-gaps`：`specguard==0.4.0`，来自 `3ed61e5`，输出 `0.4.0`。
  - `--force` 装回不带分支：输出 `0.1.0`。
  - `--force …@no-such-branch`：退出码 `2`，报 `failed to fetch branch or tag`，版本仍为 `0.1.0`。
- `git diff --stat` 只涉及 README.md、README.en.md、docs/install.md、docs/operations.md、tests/unit/test_install_entry.py，未改 `src/` 和 `pyproject.toml`。
- 卸载在规划阶段已经实测，详见 research R8 到 R11：
  - 卸载服务器上的真实安装，退出码 `0`；在原终端里运行报 `No such file or directory`（退出码 `127`）；执行 `hash -r` 后，`command -v specguard` 无输出。
  - 模拟被审核仓库的 3 个文件指纹不变。
  - 重复卸载退出码 `2`。
  - 随后按文档命令装回，输出 `0.4.0`。
  - 文档修改完成后的验证记录在 `/speckit-implement` 阶段补充。
- 卸载说明实现后的验证记录：
  - `test_docs_explain_uninstall` 先确认失败（`1 failed, 12 passed`），改文档后 `tests/unit/test_install_entry.py` 为 `13 passed`，全量 `186 passed`。
  - 第 3 节照新文档在隔离目录中执行：
    - 从 `@006-branch-install-docs` 安装，输出 `0.4.0`；
    - 卸载输出 `Uninstalled 1 executable: specguard`，退出码 `0`，`bin` 目录为空；
    - 重复卸载提示 `` `specguard` is not installed ``，退出码 `2`；
    - 模拟被审核仓库的文件指纹无差异；
    - `uv cache clean specguard` 退出码 `0`。
  - 使用者在 `~/.local/bin` 的真实安装未受影响，`specguard version` 仍为 `0.4.0`。
  - 当时第 3 节没有设 `UV_CACHE_DIR`，`uv cache clean specguard` 清除了使用者本机 uv 缓存中 SpecGuard 的 126 个文件。由 T035 修正。
- T035 修正后（第 2、3 节加入 `UV_CACHE_DIR=/tmp/sg-check/cache`）的验证：
  - 空的隔离缓存加在线安装：因 PyPI 当时不可达（`Request failed after 4 retries`）未能装上。`uv cache clean specguard` 只作用于隔离缓存，输出 `No cache entries found`。
  - 改为把本机缓存复制到隔离缓存，再用 `--offline` 安装：
    - 安装后输出 `0.4.0`；
    - 卸载退出码 `0`，`bin` 目录为空；
    - 重复卸载退出码 `2`；
    - 模拟被审核仓库的文件指纹无差异；
    - `uv cache clean specguard` 从隔离缓存删除 63 个文件。
  - 两次运行前后，`~/.cache/uv` 的字节数都是 `82489117`，没有变化；使用者真实安装仍为 `0.4.0`。
