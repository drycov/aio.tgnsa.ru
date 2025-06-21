import os
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from app.core.constants import ENV_VARS_TO_CLEAR

app = typer.Typer(help="TGNMS Entrypoint", rich_markup_mode="rich")
console = Console()

# --- Очистка переменных окружения ---
def clean_env_vars(dry_run: bool, role: str, log_changes: bool) -> List[str]:
    cleared_vars = []
    table = Table(title="Environment Variables Cleanup", show_header=True, header_style="bold magenta")
    table.add_column("Variable", style="cyan")
    table.add_column("Action", style="green")

    for key in ENV_VARS_TO_CLEAR:
        if key in os.environ:
            action = "[yellow]Would clear[/yellow]" if dry_run else "[red]Cleared[/red]"
            table.add_row(key, action)
            cleared_vars.append(key)
            if not dry_run:
                os.environ.pop(key, None)

    if log_changes and cleared_vars:
        console.print(table)
        rprint(f"\n[bold]Total {'would be cleared' if dry_run else 'cleared'}:[/bold] {len(cleared_vars)}")

    return cleared_vars

# --- Общая логика запуска ---
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
        logger.info("🚀 [bold green]Starting Telegram Bot...[/bold green]")
        run_bot()
    elif role == "api":
        logger.info("🚀 [bold blue]Starting API Server...[/bold blue]")
        run_api()
    elif role == "scheduler":
        logger.info("🚀 [bold magenta]Starting Task Scheduler...[/bold magenta]")
        run_scheduler()

# --- Команды ---
@app.command()
def bot(
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    dev: bool = typer.Option(False, "--dev", help="Enable development mode"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't clear vars, just show"),
    log_changes: bool = typer.Option(True, "--log-changes/--no-log-changes", help="Log cleared variables"),
):
    """Run Telegram bot"""
    _run_service("bot", debug, dev, dry_run, log_changes)

@app.command()
def api(
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    dev: bool = typer.Option(False, "--dev", help="Enable development mode"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't clear vars, just show"),
    log_changes: bool = typer.Option(True, "--log-changes/--no-log-changes", help="Log cleared variables"),
):
    """Run API server"""
    _run_service("api", debug, dev, dry_run, log_changes)

@app.command()
def scheduler(
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    dev: bool = typer.Option(False, "--dev", help="Enable development mode"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't clear vars, just show"),
    log_changes: bool = typer.Option(True, "--log-changes/--no-log-changes", help="Log cleared variables"),
):
    """Run background scheduler"""
    _run_service("scheduler", debug, dev, dry_run, log_changes)

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

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Show version and exit",
        callback=lambda v: _version_callback(v),
        is_eager=True,
    )
):
    """TGNMS Management System"""
    pass

def _version_callback(value: bool):
    if value:
        from app.core.config import settings
        console.print(f"[bold]{settings.app.APP_NAME}[/bold] version [green]{settings.VERSION}[/green]")
        raise typer.Exit()
