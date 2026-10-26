from pathlib import Path

import typer

from specguard import __version__
from specguard.cli.exit_codes import INTERNAL, USAGE
from specguard.config.loader import load_config
from specguard.config.models import SpecGuardConfig
from specguard.errors import ConfigError, SpecGuardError, UsageError
from specguard.pipeline import run_review

app = typer.Typer(no_args_is_help=True, add_completion=False)
config_app = typer.Typer(no_args_is_help=True)
app.add_typer(config_app, name="config")


@app.command()
def version() -> None:
    """打印产品版本，不运行审核。"""
    typer.echo(__version__)


@config_app.command("validate")
def validate(config: Path = typer.Option(..., "--config", exists=True, dir_okay=False)) -> None:
    """只校验配置，不运行检查。"""
    try:
        load_config(config)
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(USAGE) from exc
    typer.echo("配置可用")


def _apply_overrides(
    loaded: SpecGuardConfig,
    change: str | None,
    base: str | None,
    target: str | None,
    include_worktree: bool,
    mode: str | None,
    policy: str | None,
    formats: str | None,
    output: str | None,
    subject: str | None = None,
    baseline: bool = False,
) -> SpecGuardConfig:
    data = loaded.model_dump()
    if loaded.artifacts is not None and "openspec" not in loaded.model_fields_set:
        data.pop("openspec", None)
    if baseline and (change is not None or subject is not None or loaded.artifact_provider_config().subject):
        raise ConfigError("--baseline 与变更选择冲突")
    if baseline:
        provider = loaded.artifact_provider_config()
        if provider.provider not in {"openspec", "auto"}:
            raise ConfigError("--baseline 仅适用于 OpenSpec 提供方")
        data["artifacts"] = {
            "provider": "openspec",
            "root": provider.root or "openspec",
            "subject": None,
            "subject_kind": "current",
            "include_context": provider.include_context,
        }
        if data.get("openspec") is not None:
            data["openspec"]["change"] = None
    if change is not None:
        provider = loaded.artifact_provider_config().provider
        if provider not in {"openspec", "auto"}:
            raise ConfigError("--change 仅适用于 OpenSpec 提供方")
        if subject is not None and subject != change:
            raise ConfigError("--change 与 --subject 选择冲突")
        if data["artifacts"] is not None:
            data["artifacts"]["provider"] = "openspec"
            data["artifacts"]["subject"] = change
            if "openspec" in loaded.model_fields_set:
                data["openspec"]["change"] = change
        elif data.get("openspec") is None:
            data["openspec"] = {"change": change}
        else:
            data["openspec"]["change"] = change
    if base is not None:
        data["git"]["base"] = base
    if target is not None:
        data["git"]["target"] = target
    if include_worktree:
        data["git"]["include_worktree"] = True
    if mode is not None:
        data["review"]["mode"] = mode
    if policy is not None:
        data["review"]["policy"] = policy
    if formats is not None:
        data["report"]["formats"] = [item.strip() for item in formats.split(",") if item.strip()]
    if output is not None:
        data["report"]["output_dir"] = output
    try:
        return SpecGuardConfig.model_validate(data)
    except Exception as exc:
        raise ConfigError(str(exc)) from exc


@app.command()
def review(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    change: str | None = typer.Option(None, "--change"),
    subject: str | None = typer.Option(None, "--subject"),
    base: str | None = typer.Option(None, "--base"),
    target: str | None = typer.Option(None, "--target"),
    include_worktree: bool = typer.Option(False, "--include-worktree"),
    mode: str | None = typer.Option(None, "--mode"),
    policy: str | None = typer.Option(None, "--policy"),
    formats: str | None = typer.Option(None, "--format"),
    output: str | None = typer.Option(None, "--output"),
    baseline: bool = typer.Option(False, "--baseline"),
) -> None:
    """对选定变更或当前规范执行一次只读审核。"""
    try:
        loaded = _apply_overrides(
            load_config(config),
            change,
            base,
            target,
            include_worktree,
            mode,
            policy,
            formats,
            output,
            subject,
            baseline,
        )
        report, code = run_review(
            loaded,
            config,
            cli_subject=None if baseline else (subject or change),
            baseline=baseline,
        )
    except (ConfigError, UsageError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(USAGE) from exc
    except SpecGuardError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(INTERNAL) from exc
    for path in report.metadata.output_paths:
        typer.echo(path)
    raise typer.Exit(code)
