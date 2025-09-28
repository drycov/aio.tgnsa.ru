import os
import subprocess
from typing import Any, Optional
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pydantic_settings import BaseSettings

from app import __version__
from app.core.applcm_manager import AppLifecycleManager
from app.core.constants import ENV_VARS_TO_CLEAR
from app.core.integrations import register_integrations
from app.core.logging_setup import configure_logger, logger
from app.core.plugin_manager.manager import PluginManager
from app.core.config import settings
from app.core.globals import flags

# --- Globals & Constants ---
app = typer.Typer(help="TGNMS Entrypoint", rich_markup_mode="rich")
console = Console()
plugin_manager: Optional[PluginManager] = None
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.tgnmsrc")

# -------------------- Utils --------------------


def resolve_debug_mode(cli_debug: Optional[bool] = None) -> bool:
    """Определяет режим DEBUG: CLI > ENV > settings."""
    if cli_debug is not None:
        return cli_debug
    env_debug = os.getenv("DEBUG", "").strip().lower() in ("1", "true", "yes")
    return bool(settings.DEBUG) or env_debug


def extract_env_from_model(model: BaseSettings, prefix: str = "") -> dict[str, Any]:
    """Рекурсивное извлечение переменных окружения из pydantic-модели."""
    result = {}
    for key, value in model.model_dump().items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, BaseSettings):
            result.update(extract_env_from_model(value, prefix=full_key))
        else:
            result[full_key] = value
    return result


class RoleType(str, Enum):
    bot = "bot"
    api = "api"
    scheduler = "scheduler"

    def run(self, lifecycle: AppLifecycleManager):
        """Запуск сервиса в зависимости от роли."""
        if self is RoleType.bot:
            from app.bot.runner import run_bot
            run_bot(lifecycle)
        elif self is RoleType.api:
            from app.api.server import start_api
            start_api(lifecycle)
        elif self is RoleType.scheduler:
            from app.scheduler.jobs import run_scheduler
            run_scheduler(lifecycle)


def _load_custom_env(path: Optional[str] = None):
    env_file = path or os.getenv("TGNMS_ENV_FILE") or DEFAULT_CONFIG_PATH
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v)
        console.print(f"[green]Loaded environment from:[/green] {env_file}")
    else:
        console.print(f"[yellow]Environment file not found:[/yellow] {env_file}")


def clean_env_vars(
    dry_run: bool,
    role: str,
    log_changes: bool = True,
    env_vars: list[str] = ENV_VARS_TO_CLEAR,
) -> list[str]:
    """Очищает переменные окружения перед запуском сервиса."""
    cleared_vars = []
    table = Table(title=f"Environment Cleanup for [bold]{role}[/bold]") if log_changes else None
    if table:
        table.add_column("Variable", style="cyan")
        table.add_column("Action", style="green")

    for key in env_vars:
        if key in os.environ:
            action = "[yellow]Would clear[/yellow]" if dry_run else "[red]Cleared[/red]"
            if table:
                table.add_row(key, action)
            cleared_vars.append(key)
            if not dry_run:
                os.environ.pop(key)

    if table and cleared_vars:
        console.print(table)
        rprint(f"[bold]{'Would clear' if dry_run else 'Cleared'}:[/bold] {len(cleared_vars)} variables")

    return cleared_vars


def _run_service(role: RoleType, debug: bool, dev: bool, dry_run: bool, log_changes: bool):
    os.environ["APP_ROLE"] = role.value
    lifecycle = AppLifecycleManager()
    logger.info(f"🚀 Starting {role.value.upper()}...")
    
    # 🔌 Подключаем интеграции (phpipam и любые другие)
    register_integrations(lifecycle)


    try:
        role.run(lifecycle)
    except ImportError as e:
        logger.error(f"❌ Failed to import service module for {role.value}: {e}")
        raise typer.Abort()


def _get_plugins() -> PluginManager:
    global plugin_manager
    if plugin_manager is None:
        plugin_manager = PluginManager.get_instance()
    if not plugin_manager.is_initialized:
        plugin_manager.ensure_ready()
    return plugin_manager


def plugin_name_autocomplete(ctx: typer.Context, incomplete: str) -> list[str]:
    manager = _get_plugins()
    return [
        p.meta.name
        for p in getattr(manager, "sorted_plugins", [])
        if p.meta.name.lower().startswith(incomplete.lower())
    ]


# -------------------- Plugin CLI --------------------
plugins_app = typer.Typer(help="Plugin management commands")


@plugins_app.command("list")
def list_plugins():
    manager = _get_plugins()
    table = Table(title="Loaded Plugins")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Version", style="green", no_wrap=True)
    table.add_column("Author", style="yellow", no_wrap=True)

    for plugin in manager.sorted_plugins:
        meta = getattr(plugin, "meta", None)
        table.add_row(
            meta.name if meta else "-",
            getattr(meta, "description", "-"),
            getattr(meta, "version", "-"),
            getattr(meta, "author", "-"),
        )

    console.print(table)


@plugins_app.command("enable")
def enable_plugin(name: str = typer.Argument(..., autocompletion=plugin_name_autocomplete)):
    os.environ[f"PLUGIN__{name.upper()}__ENABLED"] = "1"
    rprint(f"[green]✔ Enabled plugin:[/green] {name}")


@plugins_app.command("disable")
def disable_plugin(name: str = typer.Argument(..., autocompletion=plugin_name_autocomplete)):
    os.environ[f"PLUGIN__{name.upper()}__ENABLED"] = "0"
    rprint(f"[red]✖ Disabled plugin:[/red] {name}")


# -------------------- Env CLI --------------------
env_app = typer.Typer(help="Environment variable commands")


@env_app.command("list")
def list_env():
    """Показывает все конфигурационные переменные и их текущие значения."""
    table = Table(title="📦 TGNMS Configuration Variables", header_style="bold green")
    table.add_column("Key", style="cyan")
    table.add_column("Set in ENV?", justify="center")
    table.add_column("Effective Value", style="magenta")

    sections = {
        "app": settings.app,
        "api": settings.api,
        "bot": settings.bot,
        "db": settings.db,
        "security": settings.security,
        "net": settings.net,
        "misc": settings.misc,
    }
    if settings.USE_REDIS and hasattr(settings, "redis"):
        sections["redis"] = settings.redis
    if settings.USE_MONGODB and hasattr(settings, "mongo"):
        sections["mongo"] = settings.mongo

    for section, model in sections.items():
        config_map = extract_env_from_model(model, prefix=section)
        for key_path, effective_value in config_map.items():
            env_key = "__".join(p.upper() for p in key_path.split("."))
            is_set = env_key in os.environ
            table.add_row(key_path, "✅" if is_set else "❌", str(effective_value))

    console.print(table)


@env_app.command("diagnose")
def diagnose_env():
    from app.core.utils.diagnostics import full_settings_diagnose
    full_settings_diagnose(settings)


# -------------------- Dev CLI --------------------
dev_app = typer.Typer(help="Development utilities")


@dev_app.command("run")
def dev_run(role: RoleType = typer.Option(RoleType.api, help="Role to run in dev mode")):
    try:
        subprocess.run([
            "watchmedo", "auto-restart",
            "--patterns=*.py",
            "--recursive",
            "--directory=app",
            "--",
            "python", "-m", "app.cli", "service", "run", role.value, "--debug", "--dev",
        ])
    except FileNotFoundError:
        console.print("[bold red]watchdog/watchmedo is not installed. Use: pip install watchdog[/bold red]")


# -------------------- Service CLI --------------------
service_app = typer.Typer(help="Service runner commands")


@service_app.command("run")
def run(
    role: RoleType = typer.Argument(..., help="Service role: bot | api | scheduler"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
    dev: bool = typer.Option(False, help="Enable development mode"),
    dry_run: bool = typer.Option(False, help="Dry run environment cleanup"),
    log_changes: bool = typer.Option(True, help="Log environment changes"),
):
    debug_mode = resolve_debug_mode(debug)
    os.environ["DEBUG"] = "1" if debug_mode else "0"

    local_logger = configure_logger(debug=debug_mode).bind(component="cli")
    globals()["logger"] = local_logger  # обновляем глобальный

    _run_service(role, debug_mode, dev, dry_run, log_changes)


# -------------------- CLI Entrypoint --------------------
app.add_typer(service_app, name="service")
app.add_typer(plugins_app, name="plugins")
app.add_typer(env_app, name="env")
app.add_typer(dev_app, name="dev")


@app.command()
def completion(shell: Optional[str] = typer.Argument(None)):
    typer.echo(app.get_completion(shell or "bash"))


@app.command()
def version():
    console.print(f"[bold]TGNMS version:[/bold] [green]{__version__}[/green]")


@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", help="Show version and exit", is_eager=True),
    config: Optional[str] = typer.Option(None, "--config", help="Path to env override file"),
):
    if config:
        _load_custom_env(config)
    elif os.path.exists(DEFAULT_CONFIG_PATH):
        _load_custom_env(DEFAULT_CONFIG_PATH)

    if version:
        console.print(f"[bold]{settings.app.name}[/bold] version [green]{settings.VERSION}[/green]")
        raise typer.Exit()

    flags.debug_mode = resolve_debug_mode()
