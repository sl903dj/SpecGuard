# SpecGuard

[English](README.en.md)

SpecGuard 是本地只读的变更质量门。它审核一份 OpenSpec 变更，并给出带证据的报告。报告回答需求符合性、任务完整性、代码风险、测试有效性和审核效率。是否接受变更由工程师决定。默认不阻止合并。

## 安装

```bash
uv tool install "git+https://github.com/sl903dj/SpecGuard"
```

验证本地源码时，把 `<checkout>` 换成源码检出的绝对路径，再进入一个没有 `src/specguard` 的目录：

```bash
uv tool install --force <checkout>
mkdir -p /tmp/specguard-install-check
cd /tmp/specguard-install-check
specguard version
```

安装和运行的其余步骤见 [docs/install.md](docs/install.md)。不能访问 GitHub 或 PyPI 时，按 [内网离线安装](docs/install.md#offline-install) 把源码和依赖轮子手工传入内网。

## 许可证

Apache-2.0。全文见 [LICENSE](LICENSE)。
