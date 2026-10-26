# SpecGuard

[中文](README.md)

SpecGuard is a local, read-only quality gate for one OpenSpec change or Spec Kit feature. Its report answers requirement conformance, task completeness, code risk, test effectiveness, and review efficiency, and each conclusion carries evidence. An engineer decides whether to accept the change. The default policy does not block a merge.

## Artifact providers

Set `artifacts.provider` to `openspec`, `speckit`, or `auto`. Use `--subject <feature-directory>` to select a Spec Kit feature. Selection precedence is CLI, configuration, then `.specify/feature.json`; if none of these is present, SpecGuard exits with code `4` before checks or report writes.

Version 0.2 retains the legacy OpenSpec configuration and `--change` alias. New integrations should use `artifacts.subject` / `--subject` and report schema 1.1 `subject_id`; `metadata.change` and `artifacts.selected_change` are compatibility aliases.

Version 0.3 reviews a current OpenSpec at `openspec/specs/<capability>/spec.md`. Set `artifacts.subject_kind: current` or pass `--baseline`. If that tree and an in-progress change both exist and neither is selected, review exits `4` and tells you to use `--baseline` or `--change`. Reports use schema `1.2`.

## Install

```bash
uv tool install "git+https://github.com/sl903dj/SpecGuard"
```

To verify a local checkout, replace `<checkout>` with its absolute path, then run the command from a directory that does not contain `src/specguard`:

```bash
uv tool install --force <checkout>
mkdir -p /tmp/specguard-install-check
cd /tmp/specguard-install-check
specguard version
```

Further install and run steps are in [docs/install.md](docs/install.md). When the machine cannot reach GitHub or PyPI, follow [offline install](docs/install.md#offline-install) and carry the source plus dependency wheels in by hand.

After install, follow the steps in [docs/usage.md](docs/usage.md). That guide is in Chinese.

## License

Apache-2.0. The full text is in [LICENSE](LICENSE).
