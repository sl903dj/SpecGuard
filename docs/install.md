# 安装 SpecGuard

使用者把 `specguard` 安装到命令路径，然后到被审核的 Java 仓库里运行。该仓库不包含 SpecGuard 源码，也不把 SpecGuard 源码克隆进去。

v0.1 的安装入口是 Python 控制台脚本，不要求原生二进制。

## 使用者

从 GitHub 安装：

```bash
uv tool install "git+https://github.com/sl903dj/SpecGuard"
```

这条命令安装 GitHub 默认分支 `master`。未合并到 `master` 的功能分支不在其中，安装方法见 [安装指定分支](#branch-install)。

安装完成后，到被审核仓库里按 [docs/usage.md](usage.md) 运行。该仓库需要自己的 Git 历史、`specguard.yaml`，以及一种需求工件：OpenSpec 进行中的变更、`openspec/specs/` 下的当前规范，或 Spec Kit 功能。操作、排障和内网辅助审查见 [docs/operations.md](operations.md)。

### 安装指定分支

<a id="branch-install"></a>

功能分支不合并到 `master` 时，在地址后面加 `@<分支名>`。整段地址加引号；分支名含斜杠时直接写在 `@` 后面。

```bash
uv tool install "git+https://github.com/sl903dj/SpecGuard@<分支名>"
```

例如安装 `005-close-review-gaps`：

```bash
uv tool install "git+https://github.com/sl903dj/SpecGuard@005-close-review-gaps"
specguard version
```

`specguard version` 输出 `0.4.0`。

已经装过 SpecGuard 时，改装另一个分支，或同一分支有了新提交要更新，都用加 `--force` 的命令：

```bash
uv tool install --force "git+https://github.com/sl903dj/SpecGuard@<分支名>"
```

装回 `master`：

```bash
uv tool install --force "git+https://github.com/sl903dj/SpecGuard"
```

`uv tool upgrade` 不会取得分支上的新提交，不要用它更新按分支安装的 SpecGuard。

查看可安装的分支名：

```bash
git ls-remote --heads https://github.com/sl903dj/SpecGuard
```

也可以打开 <https://github.com/sl903dj/SpecGuard/branches>。分支名写错或远端没有该分支时安装失败，已装的版本保持不变。分支已删除或已合并到 `master` 时，改用不带分支的命令。

不能访问 GitHub 时，带分支的地址同样不可用，按 [内网离线安装](#offline-install) 处理。

## 验证本地源码

把 `<checkout>` 换成 SpecGuard 源码检出的绝对路径。安装之后，先离开源码检出再运行 `specguard version`。下面的空目录是当前工作目录，不是安装位置，命令不往里面写文件。

```bash
uv tool install --force <checkout>
mkdir -p /tmp/specguard-install-check
cd /tmp/specguard-install-check
specguard version
```

`/tmp/specguard-install-check` 里没有 `src/specguard`。`specguard version` 的输出与所装分支或检出的 `pyproject.toml` 版本一致，例如 `master` 为 `0.1.0`，`005-close-review-gaps` 为 `0.4.0`。

## 内网离线安装

<a id="offline-install"></a>

内网电脑不能访问 GitHub 或 PyPI 时，不要使用上面的 Git 地址。在能访问外网的电脑上取得源码和依赖轮子，再手工传入内网。内网安装不再访问 `github.com` 或 `pypi.org`。

内网机预先具备 Python 3.11 或更高版本，以及 `uv`。

直接依赖：

- `typer>=0.12`
- `pydantic>=2`
- `httpx>=0.27`
- `pyyaml>=6`

轮子目录必须包含这些包的传递依赖，不能只拷贝上面四个名字。`pytest` 是开发依赖，安装命令不需要它。

从检出根目录安装时，`uv` 会按 `pyproject.toml` 的 `[build-system] requires` 本地构建。构建依赖是 `setuptools>=68`，它不是运行时依赖，`uv export` 不会把它写进 `requirements.txt`，必须单独下载进轮子目录。

外网准备时，把 `<分支名>` 换成要传入内网的分支。不加 `--branch` 时取默认分支 `master`。之后的 `uv lock` 和 `uv export` 都在这个检出里执行，依赖跟随所选分支。

```bash
git clone --branch <分支名> https://github.com/sl903dj/SpecGuard.git
cd SpecGuard
uv lock
uv export --frozen --no-dev --no-emit-project -o requirements.txt
uv venv /tmp/specguard-fetch
uv pip install --python /tmp/specguard-fetch/bin/python pip
/tmp/specguard-fetch/bin/python -m pip download -r requirements.txt "setuptools>=68" -d /tmp/specguard-wheels
```

把克隆得到的 `SpecGuard` 目录和 `/tmp/specguard-wheels` 手工拷进内网。`<检出根目录>` 是含有 `pyproject.toml` 的那一层。不要传入 `src/specguard`，该目录没有 `pyproject.toml`。内网安装之后，先离开源码检出再运行 `specguard version`。下面的空目录是当前工作目录，不是安装位置，命令不往里面写文件。

```bash
uv tool install --offline --no-index --find-links <轮子目录> <检出根目录>
mkdir -p /tmp/specguard-install-check
cd /tmp/specguard-install-check
specguard version
```

该目录没有 `src/specguard`。`specguard version` 的输出与所装分支或检出的 `pyproject.toml` 版本一致，例如 `master` 为 `0.1.0`，`005-close-review-gaps` 为 `0.4.0`。

## 开发者

开发和测试才使用 SpecGuard 源码检出。在含有 `pyproject.toml` 的检出根目录安装开发依赖并运行测试。不要把这个源码检出复制进被审核仓库。

```bash
uv venv
uv pip install -e ".[dev]"
.venv/bin/python -m pytest
```
