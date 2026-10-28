# SpecGuard

[中文](README.md)

SpecGuard is a local, read-only quality gate for one OpenSpec change or Spec Kit feature. Its report answers requirement conformance, task completeness, code risk, test effectiveness, and review efficiency, and each conclusion carries evidence. An engineer decides whether to accept the change. The default policy does not block a merge.

## Artifact providers

Set `artifacts.provider` to `openspec`, `speckit`, or `auto`. Use `--subject <feature-directory>` to select a Spec Kit feature. Selection precedence is CLI, configuration, then `.specify/feature.json`; if none of these is present, SpecGuard exits with code `4` before checks or report writes.

Version 0.2 retains the legacy OpenSpec configuration and `--change` alias. New integrations should use `artifacts.subject` / `--subject` and report schema 1.1 `subject_id`; `metadata.change` and `artifacts.selected_change` are compatibility aliases.

Version 0.3 reviews a current OpenSpec at `openspec/specs/<capability>/spec.md`. Set `artifacts.subject_kind: current` or pass `--baseline`. If that tree and an in-progress change both exist and neither is selected, review exits `4` and tells you to use `--baseline` or `--change`. Reports use schema `1.2`.

Version 0.4 reports use schema `1.3`. Requirement evidence and acceptance scenarios are recorded separately. An OpenSpec change is compared with the current spec, and undeclared conflicts are reported. Historical calibration is read from `calibration.json` in the report directory; completing it does not enable blocking. All nine risk classes receive a disposition. Evidence scope stays on the git range by default, and `target-tree` applies only to the current spec. When a change touches more than one build module, the report names the modules a repository-level command did not cover separately.

## Install

```bash
uv tool install "git+https://github.com/sl903dj/SpecGuard"
```

This command installs the GitHub default branch, `master`. Feature branches that are not merged into `master` are not included.

To install a feature branch, replace `<branch>` with the remote branch name:

```bash
uv tool install "git+https://github.com/sl903dj/SpecGuard@<branch>"
```

Switching to another branch, updating a branch, going back to `master`, and listing branch names are covered in [install a branch](docs/install.md#branch-install).

To verify a local checkout, replace `<checkout>` with its absolute path, then run the command from a directory that does not contain `src/specguard`:

```bash
uv tool install --force <checkout>
mkdir -p /tmp/specguard-install-check
cd /tmp/specguard-install-check
specguard version
```

To uninstall:

```bash
uv tool uninstall specguard
```

Uninstalling does not delete the configuration or reports in reviewed repositories. See [uninstall](docs/install.md#uninstall).

Further install and run steps are in [docs/install.md](docs/install.md). When the machine cannot reach GitHub or PyPI, follow [offline install](docs/install.md#offline-install) and carry the source plus dependency wheels in by hand.

After install, follow the steps in [docs/usage.md](docs/usage.md). Object selection, exit-code troubleshooting, intranet assisted review, and CI are in [docs/operations.md](docs/operations.md). Both guides are in Chinese.

## License

Apache-2.0. The full text is in [LICENSE](LICENSE).
