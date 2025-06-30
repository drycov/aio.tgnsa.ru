import asyncio
import os
import subprocess
from typing import Optional, List
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from app.core.applcm_manager import AppLifecycleManager
from app.core.constants import ENV_VARS_TO_CLEAR
from app.core.plugin_manager.manager import PluginManager
from app import __version__

app = typer.Typer(help="TGNMS Entrypoint", rich_markup_mode="rich")
console = Console()
plugin_manager = None  # глобальная переменная

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.tgnmsrc")


class RoleType(str, Enum):
    bot = "bot"
    api = "api"
    scheduler = "scheduler"


plugin_manager = None


# --- Load external environment config ---
def _load_custom_env(path: Optional[str] = None):
    """
    Load environment variables from a file.

    Args:
        path (Optional[str]): Path to env-file. If not specified, looks in $TGNMS_ENV_FILE or ~/.tgnmsrc.
    """
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


# --- Clean environment variables ---
def clean_env_vars(
    dry_run: bool,
    role: str,
    log_changes: bool,
    env_vars: List[str] = ENV_VARS_TO_CLEAR,
) -> List[str]:
    """
    Clean environment variables that may interfere with configuration.

    Args:
        dry_run (bool): If True — only logging without deletion.
        role (str): Role name (bot/api/scheduler).
        log_changes (bool): Enable logging of changes.
        env_vars (List[str]): List of variables to be cleared.

    Returns:
        List[str]: List of cleared variables.
    """
    cleared_vars: List[str] = []

    show_table = os.environ.get("DEBUG", "false").lower() in (
        "1",
        "true",
    ) or os.environ.get("DEV", "false").lower() in ("1", "true")

    table = None
    if show_table:
        table = Table(
            title=f"Environment Cleanup for [bold]{role}[/bold]",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Variable", style="cyan")
        table.add_column("Action", style="green")

    for key in env_vars:
        if key in os.environ:
            action = "[yellow]Would clear[/yellow]" if dry_run else "[red]Cleared[/red]"
            if show_table:
                table.add_row(key, action)
            cleared_vars.append(key)
            if not dry_run:
                os.environ.pop(key)

    if log_changes and cleared_vars and show_table:
        console.print(table)
        rprint(
            f"\n[bold]{'Would clear' if dry_run else 'Cleared'}:[/bold] {len(cleared_vars)} variables"
        )

    return cleared_vars


# --- Unified service runner ---
def _run_service(role: str, debug: bool, dev: bool, dry_run: bool, log_changes: bool):
    """
    Run one of the system components (bot, api, scheduler) with environment parameters.

    Args:
        role (str): Role name.
        debug (bool): Enable debug mode.
        dev (bool): Enable development mode.
        dry_run (bool): Only show which variables will be cleared.
        log_changes (bool): Log changes to variables.
    """
    clean_env_vars(dry_run, role, log_changes)

    os.environ["APP_ROLE"] = role
    if debug:
        os.environ["DEBUG"] = "True"
    if dev:
        os.environ["DEV"] = "True"

    from app.api.server import start_api
    from app.bot.runner import run_bot
    from app.scheduler.jobs import run_scheduler
    from app.core.config import logger

    lifecycle = AppLifecycleManager()

    if role == "bot":
        logger.success("\U0001f680 Starting Telegram Bot...")
        run_bot(lifecycle)
    elif role == "api":
        logger.success("\U0001f680 Starting API Server...")
        start_api(lifecycle)
    elif role == "scheduler":
        logger.success("\U0001f680 Starting Task Scheduler...")
        run_scheduler(lifecycle)


# --- Plugin Autocompletion ---
def _get_plugins() -> "PluginManager":
    """
    Синхронно получить инстанс PluginManager с гарантией инициализации.
    """
    global plugin_manager

    if plugin_manager is None:
        plugin_manager = PluginManager.get_instance()
        plugin_manager.ensure_ready()
    elif not plugin_manager.is_initialized:
        plugin_manager.ensure_ready()

    return plugin_manager


def plugin_name_autocomplete(ctx: typer.Context, incomplete: str) -> List[str]:
    """
    Автодополнение имён плагинов для CLI.
    """
    manager = _get_plugins()
    # Используем PluginBase.meta.name для безопасного доступа к имени
    return [
        plugin.meta.name
        for plugin in getattr(manager, "sorted_plugins", [])
        if plugin.meta.name.startswith(incomplete)
    ]


# --- Plugin SubApp ---
plugins_app = typer.Typer(help="Plugin management commands")


@plugins_app.command("list")
def list_plugins():
    """
    📦 List available plugins.
    """
    manager = _get_plugins()

    table = Table(title="Loaded Plugins")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Version", style="green", no_wrap=True)
    table.add_column("Author", style="magenta", no_wrap=True)

    for plugin in manager.sorted_plugins:
        table.add_row(
            plugin.name,
            plugin.description or "-",
            plugin.version or "-",
            getattr(plugin, "author", "-") or "-",
        )

    console.print(table)


@plugins_app.command("enable")
def enable_plugin(
    name: str = typer.Argument(..., autocompletion=plugin_name_autocomplete),
):
    """
    Enable the specified plugin.

    Args:
        name (str): Plugin name.
    """
    os.environ[f"PLUGIN__{name.upper()}__ENABLED"] = "1"
    rprint(f"[green]\u2714 Enabled plugin:[/green] {name}")


@plugins_app.command("disable")
def disable_plugin(
    name: str = typer.Argument(..., autocompletion=plugin_name_autocomplete),
):
    """
    Disable the specified plugin.

    Args:
        name (str): Plugin name.
    """
    os.environ[f"PLUGIN__{name.upper()}__ENABLED"] = "0"
    rprint(f"[red]\u2716 Disabled plugin:[/red] {name}")


# --- Env SubApp ---
env_app = typer.Typer(help="Environment variable commands")


@env_app.command("list")
def list_env():
    """
    List managed environment variables and their current values.
    """
    table = Table(title="TGNMS Environment Variables", header_style="bold green")
    table.add_column("Variable")
    table.add_column("Set?", justify="center")
    table.add_column("Value")

    for var in ENV_VARS_TO_CLEAR:
        value = os.environ.get(var)
        table.add_row(var, "✅" if value else "❌", value or "-")

    console.print(table)


# --- Dev SubApp ---
dev_app = typer.Typer(help="Development utilities")


@dev_app.command("run")
def dev_run():
    """
    Run API with hot-reload in development mode (watchdog).
    """
    try:
        subprocess.run(
            [
                "watchmedo",
                "auto-restart",
                "--patterns=*.py",
                "--recursive",
                "--directory=app",
                "--",
                "python",
                "-m",
                "app.cli",
                "service",
                "run",
                "api",
                "--debug",
                "--dev",
            ]
        )
    except FileNotFoundError:
        console.print(
            "[bold red]watchdog/watchmedo is not installed. Use: pip install watchdog[/bold red]"
        )


# --- Service SubApp ---
service_app = typer.Typer(help="Service runner commands")


@service_app.command("run")
def run(
    role: RoleType = typer.Argument(
        ..., help="Service role: [bold]bot[/], [bold]api[/], or [bold]scheduler[/]"
    ),
    debug: bool = typer.Option(False, help="Enable debug mode"),
    dev: bool = typer.Option(False, help="Enable development mode"),
    dry_run: bool = typer.Option(False, help="Dry run environment cleanup"),
    log_changes: bool = typer.Option(True, help="Log environment changes"),
):
    """
    Run the selected service within TGNMS (bot, API, or scheduler).

    Args:
        role (RoleType): Selected service role.
        debug (bool): Enable debug mode.
        dev (bool): Enable dev mode.
        dry_run (bool): Do not perform cleanup (only show).
        log_changes (bool): Log information about cleared variables.
    """
    _run_service(role, debug, dev, dry_run, log_changes)


# Register SubApps
app.add_typer(service_app, name="service")
app.add_typer(plugins_app, name="plugins")
app.add_typer(env_app, name="env")
app.add_typer(dev_app, name="dev")


@app.command()
def completion(shell: Optional[str] = typer.Argument(None)):
    """
    Generate shell (bash/zsh/fish/powershell) autocompletion.

    Args:
        shell (Optional[str]): Shell name (default is bash).
    """
    typer.echo(app.get_completion(shell or "bash"))


@app.command()
def version():
    """
    Show the current version of the application.
    """
    console.print(f"[bold]TGNMS version:[/bold] [green]{__version__}[/green]")


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", help="Show version and exit", is_eager=True
    ),
    config: Optional[str] = typer.Option(
        None, "--config", help="Path to env override file"
    ),
):
    """
    Main CLI flags handler.

    Args:
        version (Optional[bool]): Flag to show version and exit.
        config (Optional[str]): Path to custom environment config file.
    """
    if config:
        _load_custom_env(config)
    elif os.path.exists(DEFAULT_CONFIG_PATH):
        _load_custom_env(DEFAULT_CONFIG_PATH)

    if version:
        from app.core.config import settings

        console.print(
            f"[bold]{settings.app.APP_NAME}[/bold] version [green]{settings.VERSION}[/green]"
        )
        raise typer.Exit()
