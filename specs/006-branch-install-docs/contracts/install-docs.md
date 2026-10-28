# Contract: 安装文档的必备内容

本功能对外的接口是三份安装文档。下面每一条都由 `tests/unit/test_install_entry.py` 检查。“原文”指测试里的字符串完全匹配。

## 三份文档共同要求（README.md、README.en.md、docs/install.md）

| 编号 | 要求 | 对应需求 |
|------|------|----------|
| C1 | 保留原文 `uv tool install "git+https://github.com/sl903dj/SpecGuard"` | FR-001 |
| C2 | 含原文 `uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"`；README.en.md 用 `<branch>` 代替 `<分支名>` | FR-003 |
| C3 | 安装一节写明默认分支 `master`。中文含“默认分支”和 `master`；英文含 “default branch” 和 `master` | FR-002 |
| C4 | 说明未合并到 `master` 的功能分支要用带分支的命令安装 | FR-002 |

## docs/install.md 追加要求

| 编号 | 要求 | 对应需求 |
|------|------|----------|
| C5 | 含真实分支示例 `uv tool install "git+https://github.com/sl903dj/SpecGuard@005-close-review-gaps"` | FR-004 |
| C6 | 含改装命令 `uv tool install --force "git+https://github.com/sl903dj/SpecGuard@<分支名>"`，以及装回 `master` 的 `uv tool install --force "git+https://github.com/sl903dj/SpecGuard"` | FR-005 |
| C7 | 写明同一分支有新提交时重新运行改装命令，并写明 `uv tool upgrade` 不会取得新提交 | FR-005、Edge Cases |
| C8 | 含 `git ls-remote --heads https://github.com/sl903dj/SpecGuard` 和分支页面地址 | FR-006 |
| C9 | 写明分支名不存在时安装失败，已装版本不变 | FR-006 |
| C10 | 不含“应输出 `0.4.0`”；版本核对写明“与所装分支一致”，并举例 `master` 为 `0.1.0` | FR-007 |
| C11 | 离线一节含 `git clone --branch <分支名> https://github.com/sl903dj/SpecGuard.git`，并写明不加 `--branch` 时取 `master` | FR-008 |
| C12 | 写明不能访问 GitHub 时，带分支的地址同样不可用，应改走离线安装 | Edge Cases |

## docs/operations.md

| 编号 | 要求 | 对应需求 |
|------|------|----------|
| C13 | 两处版本核对不再把 `0.4.0` 写成任何安装的固定结果，改为与所装分支一致 | FR-007 |

## 不变项

- 现有 `test_install_entry.py` 的全部断言继续通过。
- 包版本保持 `0.4.0`，CLI 行为不变（FR-010）。
- README.en.md 与 README.md 安装一节的条目一一对应（FR-009）。
