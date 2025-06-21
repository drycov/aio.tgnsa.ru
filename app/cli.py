import os
import subprocess
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from app.core.constants import ENV_VARS_TO_CLEAR
from app.plugins.manager import PluginManager

app = typer.Typer(help="TGNMS Entrypoint", rich_markup_mode="rich")
console = Console()

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.tgnmsrc")

# --- Load external environment config ---
def _load_custom_env(path: Optional[str]):
    env_file = path or os.getenv("TGNMS_ENV_FILE") or DEFAULT_CONFIG_PATH
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v)

# --- Clean environment variables ---
def clean_env_vars(
    dry_run: bool,
    role: str,
    log_changes: bool,
    env_vars: List[str] = ENV_VARS_TO_CLEAR,
) -> List[str]:
    cleared_vars: List[str] = []

    show_table = os.getenv("DEBUG", "false").lower() in ("1", "true") or \
                 os.getenv("DEV", "false").lower() in ("1", "true")

    table = None
    if show_table:
        table = Table(
            title=f"Environment Cleanup for [bold]{role}[/bold]",
            show_header=True,
            header_style="bold magenta"
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
        rprint(f"\n[bold]{'Would clear' if dry_run else 'Cleared'}:[/bold] {len(cleared_vars)} variables")

    return cleared_vars

# --- Unified service runner ---
def _run_service(role: str, debug: bool, dev: bool, dry_run: bool, log_changes: bool):
    clean_env_vars(dry_run, role, log_changes)

    os.environ["APP_ROLE"] = role
    if debug:
        os.environ["DEBUG"] = "True"
    if dev:
        os.environ["DEV"] = "True"

    from app.api.server import run_api
    from app.bot.runner import run_bot
    from app.scheduler.jobs import run_scheduler
    from app.core.config import logger

    if role == "bot":
        logger.info("\U0001F680 [bold green]Starting Telegram Bot...[/bold green]")
        run_bot()
    elif role == "api":
        logger.info("\U0001F680 [bold blue]Starting API Server...[/bold blue]")
        run_api()
    elif role == "scheduler":
        logger.info("\U0001F680 [bold magenta]Starting Task Scheduler...[/bold magenta]")
        run_scheduler()

# --- Plugin Autocompletion ---
def plugin_name_autocomplete(ctx: typer.Context, incomplete: str):
    manager = PluginManager()
    manager.load_all()
    return [plugin.name for plugin in manager.sorted_plugins if plugin.name.startswith(incomplete)]

# --- Commands ---
@app.command()
def bot(debug: bool = False, dev: bool = False, dry_run: bool = False, log_changes: bool = True):
    """Run Telegram bot"""
    _run_service("bot", debug, dev, dry_run, log_changes)

@app.command()
def api(debug: bool = False, dev: bool = False, dry_run: bool = False, log_changes: bool = True):
    """Run API server"""
    _run_service("api", debug, dev, dry_run, log_changes)

@app.command()
def scheduler(debug: bool = False, dev: bool = False, dry_run: bool = False, log_changes: bool = True):
    """Run background scheduler"""
    _run_service("scheduler", debug, dev, dry_run, log_changes)

@app.command("plugins:list")
def list_plugins():
    """\U0001F4E6 List available plugins"""
    manager = PluginManager()
    manager.load_all()

    table = Table(title="Loaded Plugins")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")

    for plugin in manager.sorted_plugins:
        table.add_row(plugin.name, getattr(plugin, "description", "-"))

    console.print(table)

@app.command("plugins:enable")
def enable_plugin(name: str = typer.Argument(..., autocompletion=plugin_name_autocomplete)):
    """Enable a plugin by name"""
    rprint(f"[green]\u2714 Enabled plugin:[/green] {name} (persist this manually)")

@app.command("plugins:disable")
def disable_plugin(name: str = typer.Argument(..., autocompletion=plugin_name_autocomplete)):
    """Disable a plugin by name"""
    rprint(f"[red]\u2716 Disabled plugin:[/red] {name} (persist this manually)")

@app.command("env:list")
def list_env():
    """List all managed environment variables and their current values"""
    table = Table(title="TGNMS Environment Variables", header_style="bold green")
    table.add_column("Variable")
    table.add_column("Set?", justify="center")
    table.add_column("Value")

    for var in ENV_VARS_TO_CLEAR:
        value = os.getenv(var)
        table.add_row(var, "✅" if value else "❌", value or "-")

    console.print(table)

@app.command("dev:run")
def dev_run():
    """Run with hot-reload using watchdog"""
    try:
        subprocess.run([
            "watchmedo", "auto-restart",
            "--patterns=*.py",
            "--recursive",
            "--directory=app",
            "--", "python", "-m", "app.cli", "api",
            "--debug", "--dev"
        ])
    except FileNotFoundError:
        console.print("[bold red]watchdog/watchmedo is not installed. Use: pip install watchdog[/bold red]")

@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", help="Show version and exit", is_eager=True),
    config: Optional[str] = typer.Option(None, "--config", help="Path to env override file")
):
    if config:
        _load_custom_env(config)
    elif os.path.exists(DEFAULT_CONFIG_PATH):
        _load_custom_env(DEFAULT_CONFIG_PATH)

    if version:
        from app.core.config import settings
        console.print(f"[bold]{settings.app.APP_NAME}[/bold] version [green]{settings.VERSION}[/green]")
        raise typer.Exit()
