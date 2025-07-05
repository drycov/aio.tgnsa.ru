import asyncio
import os
import subprocess
from typing import Any, Optional, List
from enum import Enum

from pydantic_settings import BaseSettings
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from app.core.applcm_manager import AppLifecycleManager
from app.core.constants import ENV_VARS_TO_CLEAR
from app.core.logging_setup import configure_logger
from app.core.plugin_manager.manager import PluginManager
from app import __version__
from app.core.validators import validate_all_settings
from app.core.config import settings
# --- Globals & Constants ---
app = typer.Typer(help="TGNMS Entrypoint", rich_markup_mode="rich")
console = Console()

logger = configure_logger().bind(component="cli")


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.tgnmsrc")
plugin_manager = None

def extract_env_from_model(model: BaseSettings, prefix: str = "") -> dict[str, Any]:
    """
    Рекурсивно извлекает переменные окружения и их значения из модели.

    Args:
        model (BaseSettings): pydantic-модель настроек
        prefix (str): текущий префикс для вложенных ключей

    Returns:
        dict[str, Any]: словарь переменных и значений
    """
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


# --- Load .env ---
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


# --- Clean ENV ---
def clean_env_vars(
    dry_run: bool,
    role: str,
    log_changes: bool,
    env_vars: List[str] = ENV_VARS_TO_CLEAR,
) -> List[str]:
    cleared_vars = []
    show_table = os.environ.get("DEBUG", "false").lower() in ("1", "true") or os.environ.get("DEV", "false").lower() in ("1", "true")

    table = Table(title=f"Environment Cleanup for [bold]{role}[/bold]", show_header=True, header_style="bold magenta") if show_table else None
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

    if log_changes and cleared_vars and table:
        console.print(table)
        rprint(f"\n[bold]{'Would clear' if dry_run else 'Cleared'}:[/bold] {len(cleared_vars)} variables")

    return cleared_vars


# --- Service Launcher ---
def _run_service(role: str, debug: bool, dev: bool, dry_run: bool, log_changes: bool):
    clean_env_vars(dry_run, role, log_changes)

    os.environ["APP_ROLE"] = role
    if debug:
        os.environ["DEBUG"] = "True"
    if dev:
        os.environ["DEV"] = "True"

    from app.api.server import start_api
    from app.bot.runner import run_bot
    from app.scheduler.jobs import run_scheduler

    lifecycle = AppLifecycleManager()
    if role == "bot":
        logger.info("\U0001f680 Starting Telegram Bot...")
        run_bot(lifecycle)
    elif role == "api":
        logger.info("\U0001f680 Starting API Server...")
        start_api(lifecycle)
    elif role == "scheduler":
        logger.info("\U0001f680 Starting Task Scheduler...")
        run_scheduler(lifecycle)


# --- Plugin Manager ---
def _get_plugins() -> PluginManager:
    global plugin_manager
    if plugin_manager is None:
        plugin_manager = PluginManager.get_instance()
    if not plugin_manager.is_initialized:
        plugin_manager.ensure_ready()
    return plugin_manager


def plugin_name_autocomplete(ctx: typer.Context, incomplete: str) -> List[str]:
    return [p.meta.name for p in getattr(_get_plugins(), "sorted_plugins", []) if p.meta.name.startswith(incomplete)]


# --- Plugin CLI ---
plugins_app = typer.Typer(help="Plugin management commands")

@plugins_app.command("list")
def list_plugins():
    manager = _get_plugins()
    table = Table(title="Loaded Plugins")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Version", style="green", no_wrap=True)
    table.add_column("Author", style="magenta", no_wrap=True)

    for plugin in manager.sorted_plugins:
        table.add_row(plugin.name, plugin.description or "-", plugin.version or "-", getattr(plugin, "author", "-") or "-")

    console.print(table)


@plugins_app.command("enable")
def enable_plugin(name: str = typer.Argument(..., autocompletion=plugin_name_autocomplete)):
    os.environ[f"PLUGIN__{name.upper()}__ENABLED"] = "1"
    rprint(f"[green]\u2714 Enabled plugin:[/green] {name}")


@plugins_app.command("disable")
def disable_plugin(name: str = typer.Argument(..., autocompletion=plugin_name_autocomplete)):
    os.environ[f"PLUGIN__{name.upper()}__ENABLED"] = "0"
    rprint(f"[red]\u2716 Disabled plugin:[/red] {name}")


# --- Env CLI ---
env_app = typer.Typer(help="Environment variable commands")

@env_app.command("list")
def list_env():
    """
    📄 Показать все конфигурационные переменные и их текущее значение.
    """
    table = Table(title="📦 TGNMS Configuration Variables", header_style="bold green")
    table.add_column("Key", style="cyan")
    table.add_column("Set in ENV?", justify="center")
    table.add_column("Effective Value", style="magenta")

    def check_env_match(key_path: str, effective_val: Any) -> tuple[str, bool]:
        """
        Проверяет, установлена ли переменная через окружение.
        Возвращает значение и флаг.
        """
        # Убрать вложенные точки (.) — привести к переменной окружения вида SECTION__KEY
        parts = key_path.split(".")
        env_key = "__".join(part.upper() for part in parts)
        env_value = os.getenv(env_key)
        return env_value if env_value is not None else "-", env_value is not None

    # Сбор переменных из всех секций settings
    sections = {
        "app": settings.app,
        "api": settings.api,
        "bot": settings.bot,
        "db": settings.db,
        "security": settings.security,
        "net": settings.net,
        "misc": settings.misc,
    }
    if settings.USE_REDIS and settings.redis:
        sections["redis"] = settings.redis
    if settings.USE_MONGODB and settings.mongo:
        sections["mongo"] = settings.mongo

    for section, model in sections.items():
        config_map = extract_env_from_model(model, prefix=section)
        for key_path, effective_value in config_map.items():
            env_val, is_set = check_env_match(key_path, effective_value)
            table.add_row(key_path, "✅" if is_set else "❌", str(effective_value))

    console.print(table)

@env_app.command("diagnose")
def diagnose_env():
    from app.core.config import settings
    from app.core.utils.diagnostics import full_settings_diagnose

    full_settings_diagnose(settings)

# --- Dev CLI ---
dev_app = typer.Typer(help="Development utilities")

@dev_app.command("run")
def dev_run():
    try:
        subprocess.run([
            "watchmedo", "auto-restart", "--patterns=*.py", "--recursive", "--directory=app",
            "--", "python", "-m", "app.cli", "service", "run", "api", "--debug", "--dev",
        ])
    except FileNotFoundError:
        console.print("[bold red]watchdog/watchmedo is not installed. Use: pip install watchdog[/bold red]")


# --- Service CLI ---
service_app = typer.Typer(help="Service runner commands")

@service_app.command("run")
def run(
    role: RoleType = typer.Argument(..., help="Service role: [bold]bot[/], [bold]api[/], or [bold]scheduler[/]"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
    dev: bool = typer.Option(False, help="Enable development mode"),
    dry_run: bool = typer.Option(False, help="Dry run environment cleanup"),
    log_changes: bool = typer.Option(True, help="Log environment changes"),
):
    _run_service(role, debug, dev, dry_run, log_changes)


# --- CLI Entrypoint ---
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
    # try:
    #     validate_all_settings()
    # except RuntimeError as e:
    #     logger.critical(f"Ошибка конфигурации при старте:\n{e}")
    #     raise typer.Exit(code=1)

    if config:
        _load_custom_env(config)
    elif os.path.exists(DEFAULT_CONFIG_PATH):
        _load_custom_env(DEFAULT_CONFIG_PATH)

    if version:
        from app.core.config import settings
        console.print(f"[bold]{settings.app.APP_NAME}[/bold] version [green]{settings.VERSION}[/green]")
        raise typer.Exit()
