# Quickstart: 验证 Spec Kit 需求来源

本指南在宪章修订并完成实现后使用。它不包含实现代码。选择规则以 [来源契约](contracts/speckit-source.md) 为准。

## 前提

- 宪章已经允许 Spec Kit 功能目录作为需求来源，并仍限制为 Java 服务端仓库。
- `specguard` 已安装。审核在被审核仓库中运行，不在 SpecGuard 源码树里把工具源码混进去。
- 样例放在 `tests/fixtures/`。

## 1. 单个 Spec Kit 功能

在只有 `specs/001-sample/spec.md` 和 `tasks.md` 的 Java 夹具中运行：

```bash
specguard review --config specguard.yaml --feature 001-sample --mode static --policy advisory
```

期望：退出码遵循现有建议模式规则；报告写明功能名 `001-sample`；含有需求覆盖和任务缺口；夹具里除报告目录外的文件和 `git status` 与审核前一致。

## 2. 多个功能必须指定

在含有两个 Spec Kit 功能、且不传 `--feature` 的夹具中运行审核。

期望：退出码 `4`，输出两个目录名，报告目录没有新文件。错误文本可以提到 `feature.json`，但不得选中其中的功能。

## 3. OpenSpec 回归

在现有单变更 OpenSpec 夹具中，不传 `--feature`，按原来的 `--change` 运行。

期望：所选变更、证据级别和只读结果与本功能加入前一致。

## 4. 两种来源同时存在

夹具同时包含一个 OpenSpec 变更和一个 Spec Kit 功能，配置里的来源保持 `auto`。

期望：退出码 `4`，输出同时提到 OpenSpec 和 Spec Kit，检查命令没有运行。

## 5. 非 Java

在使用 Spec Kit 但没有 Maven 或 Gradle 布局的夹具中指定唯一功能。

期望：报告说明代码检查不支持。需求符合性、代码风险和测试不得被写成已经通过。
