# Implementation Plan: 说明如何安装指定分支

**Branch**: `006-branch-install-docs` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-branch-install-docs/spec.md`

## Summary

不带分支的安装地址装的是默认分支 `master`，当前版本 `0.1.0`。尚未合并的功能分支，例如 `005-close-review-gaps`（`0.4.0`），没有写进文档的安装途径。另外，`docs/install.md` 把 `0.4.0` 写成了所有安装方式的预期输出。

本功能只改文档和文档检查：

- 在 README.md、README.en.md、docs/install.md 写明默认分支，并给出 `@<分支名>` 安装命令。
- 在 docs/install.md 说明如何改装、更新、装回 `master`，如何查看分支名，以及离线时如何选定分支。
- 把 docs/install.md 和 docs/operations.md 中写死的版本核对改为“与所装分支一致”。

各命令的行为已用 uv 0.13.5 实测，结果见 [research.md](research.md)。

## Technical Context

**Language/Version**: Markdown 文档；检查用 Python 3.11+

**Primary Dependencies**: 无新增；文档描述 `uv tool install` 和 `git`

**Storage**: N/A

**Testing**: pytest，扩展 `tests/unit/test_install_entry.py`

**Target Platform**: 使用者装有 `uv` 的 Linux/macOS 命令行

**Project Type**: CLI 工具的文档

**Performance Goals**: N/A

**Constraints**:

- 保留现有测试要求的原文：不带分支的安装命令、`uv tool install --force`、`https://github.com/sl903dj/SpecGuard.git`，以及离线一节的各命令。
- 不改代码，不改版本号。

**Scale/Scope**: 4 份文档（README.md、README.en.md、docs/install.md、docs/operations.md），1 个测试文件

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判断 | 说明 |
|------|------|------|
| I. 质量门，而非编程助手 | 通过 | 只改安装文档，产品定位不变 |
| II. 结论必须有证据 | 通过 | 每条命令行为都有实测记录（research R1–R6），文档不写未验证的说法 |
| III. 检查状态必须诚实 | 通过 | 不涉及检查结果 |
| IV. 辅助审查只是假设 | 通过 | 不涉及 |
| V. 默认只读且留在内部 | 通过 | 不改运行行为；文档继续保留离线安装，不要求内网访问外部 |
| 开发流程：先有失败测试 | 通过 | 先写文档检查并确认失败，再改文档（R7） |
| 开发流程：不扩大范围 | 通过 | 不含标签或提交安装，不改默认分支，不合并分支 |

Phase 1 设计后复核：没有新增违规，Complexity Tracking 为空。

## Project Structure

### Documentation (this feature)

```text
specs/006-branch-install-docs/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── install-docs.md
├── checklists/
│   └── requirements.md
└── tasks.md             # 由 /speckit-tasks 生成
```

### Source Code (repository root)

```text
README.md                         # 安装一节：默认分支说明 + @<分支名> 命令
README.en.md                      # 同上，英文，用 <branch>
docs/
├── install.md                    # 使用者一节新增“安装指定分支”；版本核对；离线 git clone --branch
└── operations.md                 # 两处版本核对改为与所装分支一致
tests/unit/
└── test_install_entry.py         # 新增契约 C1–C13 的检查
```

**Structure Decision**: 不新增文件，只改上面列出的文档和测试。docs/install.md 在“## 使用者”下新增一个子节，放分支安装、改装、更新、查看分支和失败表现。现有的“验证本地源码”“内网离线安装”“开发者”三节位置不变，便于现有测试按 `## 内网离线安装` 切分文本。

## Complexity Tracking

无。
