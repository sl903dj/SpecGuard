# Data Model: 说明如何安装指定分支

本功能不新增运行时数据。下面列出文档里要讲清楚的对象。

## 安装来源

| 来源 | 文档中的写法 | 装到的版本 |
|------|--------------|------------|
| 默认分支 | `uv tool install "git+https://github.com/sl903dj/SpecGuard"` | `master` 上的版本，当前为 `0.1.0` |
| 指定分支 | `uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"` | 该分支最新提交上的版本，例如 `005-close-review-gaps` 为 `0.4.0` |
| 本地检出 | `uv tool install --force <checkout>` | 检出所在提交的版本 |
| 离线检出 | `git clone --branch <分支名> …`，然后 `uv tool install --offline …` | 克隆时选定分支的版本；不加 `--branch` 时是 `master` |

规则：

- 每处“应输出版本”的说明都必须对应上表中的一种来源，不能只写一个固定版本号。
- 带分支的安装命令中，地址连同 `@<分支名>` 整段加引号。

## 分支名

- 指 GitHub 远端上的分支名，可以含斜杠。
- 查看方式：`https://github.com/sl903dj/SpecGuard/branches`，或 `git ls-remote --heads https://github.com/sl903dj/SpecGuard`。
- 分支名不存在时安装失败，已安装的版本保持不变。

## 安装状态变化

```text
未安装 --首次安装（任一来源）--> 已装 A
已装 A --uv tool install --force "<地址>@B"--> 已装 B
已装 B --uv tool install --force "<不带分支的地址>"--> 已装 master
已装 B --分支 B 有新提交，重新 --force 安装--> 已装 B 的新提交
已装 A --安装不存在的分支--> 安装失败，仍是 A
```

`uv tool upgrade specguard` 不会取得分支上的新提交，文档不把它作为更新方式。

## 卸载范围

| 对象 | 卸载命令是否删除 | 文档中的处理 |
|------|------------------|--------------|
| `specguard` 命令和工具环境 | 删除 | `uv tool uninstall specguard` |
| 被审核仓库的 `specguard.yaml`、`.specguard/reports/`（含 `calibration.json`） | 不删除 | 保留，需要时由使用者手工删除；文档不给删除命令 |
| uv 下载缓存 | 不删除 | 可选：`uv cache clean specguard` |
| 离线传入的源码目录和 `/tmp/specguard-wheels` | 不删除 | 需要时手工删除 |
| 开发者检出里的 `.venv` | 不删除 | 需要时删除该检出里的 `.venv` |
| 用户主目录下的配置 | 不存在 | 无需处理 |

## 卸载状态变化

```text
已装（任一来源） --uv tool uninstall specguard--> 未安装（退出码 0）
未安装 --uv tool uninstall specguard--> 提示 `specguard` is not installed（退出码 2），无其他影响
未安装 --任一安装命令--> 已装
已装 A --改装分支--> 已装 B（不需要先卸载）
```

卸载后在原终端里，shell 可能仍缓存着旧路径，运行时报 `No such file or directory`。执行 `hash -r` 或新开终端后，`command -v specguard` 无输出。
