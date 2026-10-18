# SpecGuard

[中文](README.md)

SpecGuard is a local, read-only quality gate for one OpenSpec change. Its report answers requirement conformance, task completeness, code risk, test effectiveness, and review efficiency, and each conclusion carries evidence. An engineer decides whether to accept the change. The default policy does not block a merge.

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
