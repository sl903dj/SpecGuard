# 安装 SpecGuard

使用者把 `specguard` 安装到命令路径，然后到被审核的 Java 仓库里运行。该仓库不包含 SpecGuard 源码，也不把 SpecGuard 源码克隆进去。

v0.1 的安装入口是 Python 控制台脚本，不要求原生二进制。

## 使用者

在本机安装命令。示例：

```bash
uv tool install specguard
```

安装完成后，进入被审核仓库：

```bash
specguard version
specguard config validate --config specguard.yaml
specguard review --config specguard.yaml --mode static --policy advisory
```

被审核仓库只需要自己的 Git 历史、OpenSpec 变更和 `specguard.yaml`。

## 开发者

开发和测试才使用 SpecGuard 源码检出。在本仓库安装开发依赖并运行测试。不要把这个源码检出复制进被审核仓库。
