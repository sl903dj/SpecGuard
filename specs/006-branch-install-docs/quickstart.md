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
export UV_TOOL_DIR=/tmp/sg-check/tools UV_TOOL_BIN_DIR=/tmp/sg-check/bin
uv tool install "git+https://github.com/sl903dj/SpecGuard"
/tmp/sg-check/bin/specguard version          # 预期 0.1.0（master）
uv tool install --force "git+https://github.com/sl903dj/SpecGuard@005-close-review-gaps"
/tmp/sg-check/bin/specguard version          # 预期 0.4.0
uv tool install --force "git+https://github.com/sl903dj/SpecGuard"
/tmp/sg-check/bin/specguard version          # 预期 0.1.0
uv tool install --force "git+https://github.com/sl903dj/SpecGuard@no-such-branch"   # 预期失败
/tmp/sg-check/bin/specguard version          # 预期仍是 0.1.0
git ls-remote --heads https://github.com/sl903dj/SpecGuard   # 列出可安装的分支
unset UV_TOOL_DIR UV_TOOL_BIN_DIR
rm -rf /tmp/sg-check
```

不能访问 GitHub 时，可以把地址换成 `git+file://<本地检出>`，用同样的步骤验证，分支名用本地已有的分支。

## 3. 人工通读

- README.md 和 README.en.md 安装一节的条目一一对应。
- docs/install.md 和 docs/operations.md 里每处版本核对都对应一种安装来源。

## 验证记录（2026-10-28，uv 0.13.5）

- 修改前全量测试：`181 passed`。
- 修改后：`tests/unit/test_install_entry.py` 为 `12 passed`，全量 `185 passed`。新增 4 条检查，每条都先确认失败再改文档。
- 第 2 节在隔离目录中从 GitHub 实际安装，结果如下，与文档一致：
  - 不带分支：`specguard==0.1.0`，来自 `b5d0d06`，`specguard version` 输出 `0.1.0`。
  - `--force …@005-close-review-gaps`：`specguard==0.4.0`，来自 `3ed61e5`，输出 `0.4.0`。
  - `--force` 装回不带分支：输出 `0.1.0`。
  - `--force …@no-such-branch`：退出码 `2`，报 `failed to fetch branch or tag`，版本仍为 `0.1.0`。
- `git diff --stat` 只涉及 README.md、README.en.md、docs/install.md、docs/operations.md、tests/unit/test_install_entry.py，未改 `src/` 和 `pyproject.toml`。
