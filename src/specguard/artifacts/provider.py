from pathlib import Path
from typing import Protocol

from specguard.artifacts.models import (
    ArtifactBundle,
    ArtifactProviderConfig,
    ArtifactSubject,
)
from specguard.artifacts.openspec import OpenSpecProvider
from specguard.artifacts.speckit import SpecKitProvider
from specguard.errors import UsageError


class ArtifactProvider(Protocol):
    name: str

    def discover(self, repository: Path, config: ArtifactProviderConfig) -> list[str]: ...

    def select(
        self,
        repository: Path,
        config: ArtifactProviderConfig,
        cli_subject: str | None = None,
    ) -> ArtifactSubject | None: ...

    def validate(self, subject: ArtifactSubject) -> None: ...

    def load(
        self,
        repository: Path,
        subject: ArtifactSubject,
        config: ArtifactProviderConfig,
    ) -> ArtifactBundle: ...


_PROVIDERS: dict[str, ArtifactProvider] = {
    "openspec": OpenSpecProvider(),
    "speckit": SpecKitProvider(),
}


def provider_for(name: str) -> ArtifactProvider:
    try:
        return _PROVIDERS[name]
    except KeyError as exc:
        raise UsageError(f"未知工件提供方: {name}") from exc


def resolve_provider(
    repository: Path,
    config: ArtifactProviderConfig,
) -> tuple[ArtifactProvider, ArtifactProviderConfig]:
    if config.provider != "auto":
        return provider_for(config.provider), config
    detected: list[tuple[ArtifactProvider, ArtifactProviderConfig]] = []
    for name, root in (("openspec", "openspec"), ("speckit", "specs")):
        candidate_config = config.model_copy(update={"provider": name, "root": root})
        provider = provider_for(name)
        marker = repository / (".specify" if name == "speckit" else root)
        if marker.is_dir() and provider.discover(repository, candidate_config):
            detected.append((provider, candidate_config))
    if len(detected) != 1:
        names = ", ".join(item[0].name for item in detected) or "无"
        raise UsageError(f"artifacts.provider=auto 无法唯一识别提供方（检测到: {names}）")
    return detected[0]


def load_bundle(
    repository: Path,
    config: ArtifactProviderConfig,
    cli_subject: str | None = None,
    *,
    include_main_specs: bool = True,
    require_selection: bool = True,
    baseline: bool = False,
) -> ArtifactBundle | None:
    provider, effective = resolve_provider(repository, config)
    if (
        provider.name == "openspec"
        and not require_selection
        and not baseline
        and effective.subject_kind is None
        and cli_subject is None
        and effective.subject is None
        and len(provider.discover(repository, effective)) > 1
    ):
        from specguard.artifacts.openspec import has_current_specs

        if not has_current_specs(repository, effective):
            return None
    subject = provider.select(repository, effective, cli_subject, baseline=baseline) if provider.name == "openspec" else provider.select(repository, effective, cli_subject)
    if subject is None:
        return None
    provider.validate(subject)
    if provider.name == "openspec":
        return OpenSpecProvider().load(
            repository,
            subject,
            effective,
            include_main_specs=include_main_specs,
        )
    return provider.load(repository, subject, effective)
