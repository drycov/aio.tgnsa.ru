from typing import List, Tuple
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
import logging

from app.core.config import settings

console = Console()
logger = logging.getLogger(__name__)


def _extract_validation_details(error: ValidationError) -> List[Tuple[str, str, str]]:
    """
    Парсит ValidationError в список (field_path, error_msg, error_type)
    """
    details = []
    for err in error.errors():
        loc = ".".join(map(str, err["loc"]))
        msg = err["msg"]
        err_type = err.get("type", "-")
        details.append((loc, msg, err_type))
    return details


def _validate_component(name: str, component: BaseSettings) -> Tuple[str, bool, List[Tuple[str, str, str]]]:
    """
    Выполняет строгую проверку модели и возвращает подробный результат.
    """
    try:
        _ = component.model_dump()  # trigger validation
        return name, True, [("✔", "OK", "-")]
    except ValidationError as e:
        return name, False, _extract_validation_details(e)


def validate_all_settings() -> None:
    """
    Выполняет валидацию всех секций конфига `settings`. Выбрасывает RuntimeError при ошибке.
    """
    components: List[Tuple[str, BaseSettings]] = [
        ("app", settings.app),
        ("db", settings.db),
        ("api", settings.api),
        ("bot", settings.bot),
        ("security", settings.security),
        ("net", settings.net),
        ("misc", settings.misc),
    ]

    if settings.USE_REDIS and settings.redis:
        components.append(("redis", settings.redis))
    if settings.USE_MONGODB and settings.mongo:
        components.append(("mongo", settings.mongo))

    main_table = Table(title="🔍 Configuration Validation Summary", header_style="bold green")
    main_table.add_column("Component", style="cyan", no_wrap=True)
    main_table.add_column("Status", style="bold")

    has_errors = False

    for name, component in components:
        name, success, details = _validate_component(name, component)
        status = "✅ OK" if success else f"[red]❌ {len(details)} error(s)[/red]"
        main_table.add_row(name, status)

        if not success:
            has_errors = True
            detail_table = Table(title=f"🔴 Errors in [{name}]", show_header=True, header_style="bold red")
            detail_table.add_column("Field", style="yellow", no_wrap=True)
            detail_table.add_column("Message", style="white")
            detail_table.add_column("Type", style="magenta", no_wrap=True)

            for field, msg, typ in details:
                detail_table.add_row(field, msg, typ)

            console.print(detail_table)

    console.print(main_table)

    if has_errors:

        raise RuntimeError("❌ Обнаружены ошибки валидации конфигурации.")
