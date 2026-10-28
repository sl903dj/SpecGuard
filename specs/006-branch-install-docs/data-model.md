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
