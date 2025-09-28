import os
import json
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic import SecretStr, computed_field
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings
from rich.table import Table
from rich.console import Console
import logging

from app.core.config import CONFIG_PATH, SECRETS_DICT, DATA_DIR, load_toml

logger = logging.getLogger("diagnostics")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("diagnostics.log", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

META_TABLE = Table(title="🔢 Сводная таблица конфигурации", show_lines=True)
META_TABLE.add_column("Секция", style="cyan", no_wrap=True)
META_TABLE.add_column("Поле", style="magenta")
META_TABLE.add_column("Значение", style="green")


def is_secret_annotation(annotation: Any) -> bool:
    try:
        args = get_args(annotation)
        return any(issubclass(arg, SecretStr) for arg in args if isinstance(arg, type)) or \
               issubclass(annotation, SecretStr)
    except TypeError:
        return False


def redact_secrets(val: Any) -> str:
    if isinstance(val, SecretStr):
        return "********"
    return val


def safe_str(val: Any) -> str:
    if val is None:
        return "–"
    if isinstance(val, SecretStr):
        return "********"
    if isinstance(val, (list, set, tuple)):
        return ", ".join(map(str, val)) if val else "[]"
    return str(val)


def resolve_default(field) -> str:
    if field.default is not PydanticUndefined:
        return safe_str(field.default)
    elif field.default_factory is not PydanticUndefined:
        try:
            return f"factory: {field.default_factory.__name__}"
        except AttributeError:
            return f"factory: {repr(field.default_factory)}"
    return "PydanticUndefined"


def detect_source(key: str, value: Any, section: str) -> str:
    config_section = load_toml(CONFIG_PATH).get(section, {})
    if config_section.get(key) == value:
        return f"TOML [{section}.{key}]"

    env_val = os.getenv(key)
    if env_val and str(env_val) == str(value):
        return f".env/ENV [{key}]"

    if SECRETS_DICT.get(section, {}).get(key) == value:
        return f"secrets.toml [{section}.{key}]"

    secrets_file = DATA_DIR / "secrets" / key
    if secrets_file.exists() and secrets_file.read_text().strip() == str(value):
        return f"secrets_dir [{key}]"

    return "🧹 Установлено явно / конструктор" if value else "по умолчанию / не определено"


def detect_explicit_set_fields(model: BaseSettings) -> set:
    return getattr(model, "_explicitly_set_fields", set())


def diagnose_model(model: BaseSettings, section: str = ""):
    console = Console()
    cls = type(model)
    section = section or cls.__name__.lower()
    explicit_fields = detect_explicit_set_fields(model)

    table = Table(title=f"🧪 Диагностика модели: {cls.__name__}", show_lines=True)
    table.add_column("Поле", style="cyan", no_wrap=True)
    table.add_column("Значение", style="magenta")
    table.add_column("Источник", style="green")
    table.add_column("Описание", style="white")
    table.add_column("По умолчанию", style="yellow")
    table.add_column("Secret?", style="red", justify="center")
    table.add_column("Env имя", style="blue")

    for field_name, field in cls.model_fields.items():
        value = getattr(model, field_name, None)
        annotation = field.annotation
        alias = field.alias or field_name
        is_secret = is_secret_annotation(annotation)

        # Append to meta-table
        META_TABLE.add_row(section, field_name, safe_str(redact_secrets(value)))

        table.add_row(
            safe_str(field_name),
            safe_str(redact_secrets(value)),
            safe_str(detect_source(field_name, value, section)),
            safe_str(field.description or "–"),
            resolve_default(field),
            "✅" if is_secret else "–",
            safe_str(alias),
        )

    console.print(table)
    logger.debug(f"\n{table}\n")

    if extra := getattr(model, "__pydantic_extra__", None):
        console.print(f"[bold cyan]__pydantic_extra__:[/bold cyan] {dict(extra)}")

    def safe_dump(data: dict[str, Any]) -> dict[str, Any]:
        def sanitize(val):
            if isinstance(val, SecretStr):
                return "********"
            if isinstance(val, (list, set, tuple)):
                return [sanitize(v) for v in val]
            if isinstance(val, dict):
                return {k: sanitize(v) for k, v in val.items()}
            return val

        return {k: sanitize(v) for k, v in data.items()}

    diff = model.model_dump(exclude_defaults=True)
    if diff:
        json_safe_diff = json.dumps(safe_dump(diff), ensure_ascii=False, indent=2)
        console.print(f"[bold green]Явно переопределённые значения:[/bold green]\n{json_safe_diff}")


    if explicit_fields:
        console.print(f"[bold yellow]Явно установлены:[/bold yellow] {', '.join(explicit_fields)}")
    else:
        console.print("[dim]Нет явно установленных полей[/dim]")


def full_settings_diagnose(settings: BaseSettings):
    print("\n🧹 Запуск полной диагностики всех подсекций конфигурации...")
    for attr_name in dir(settings):
        if attr_name.startswith("_"):
            continue
        attr = getattr(settings, attr_name)
        if isinstance(attr, BaseSettings):
            diagnose_model(attr, section=attr_name)
    Console().print(META_TABLE)
    logger.debug(f"\n{META_TABLE}\n")
