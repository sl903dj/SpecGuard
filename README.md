# SpecGuard

[English](README.en.md)

SpecGuard 是本地只读的变更质量门。它审核一份 OpenSpec 变更或 Spec Kit 功能，并给出带证据的报告。报告回答需求符合性、任务完整性、代码风险、测试有效性和审核效率。是否接受变更由工程师决定。默认不阻止合并。

## 工件提供方

在 `specguard.yaml` 的 `artifacts.provider` 中选择 `openspec`、`speckit` 或 `auto`。Spec Kit 用 `--subject <功能目录>` 选择对象；选择优先级为 CLI、配置、`.specify/feature.json`。三者都没有时退出 `4`，不会开始检查或写报告。

v0.2 保留 OpenSpec 的 `openspec` 配置和 `--change` 别名。新配置和报告消费者应使用 `artifacts.subject` / `--subject` 以及 schema 1.1 的 `subject_id`；`metadata.change` 和 `artifacts.selected_change` 仅为兼容字段。详见 [使用说明](docs/usage.md)。

v0.3 可以审核从零建立的当前 OpenSpec，位置是 `openspec/specs/<能力>/spec.md`。配置写 `artifacts.subject_kind: current`，或在命令中加 `--baseline`。仓库里同时有当前规范和进行中的变更、又没有明确选择时，审核退出 `4`，并提示使用 `--baseline` 或 `--change`。报告 schema 为 `1.2`。

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

安装完成后的使用步骤见 [docs/usage.md](docs/usage.md)。

## 许可证

Apache-2.0。全文见 [LICENSE](LICENSE)。
