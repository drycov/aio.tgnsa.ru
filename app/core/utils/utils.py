import datetime
import inspect
import os
import re
import tempfile
from typing import Any, Callable, Dict, Literal, Optional
import redis.asyncio as redis
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.exceptions import RedisError
import tomli_w

from app.bot.fsm.file_storage import FileStorage
from app.core.config import logger, settings
from app.core.config import DATA_DIR
from puresnmp.types import TimeTicks

from pyasn1.type.univ import OctetString
from pyasn1_modules.rfc1902 import Counter32

from pathlib import Path


def initialize_storage():
    """
    Инициализация FSM-хранилища с поддержкой Redis, файловой системы и fallback на память.
    """
    try:
        if settings.USE_REDIS:
            redis_client = redis.from_url(settings.redis.dsn())
            logger.info("✅ Используется RedisStorage")
            return RedisStorage(redis_client)

        elif settings.USE_FS:
            storage_dir = Path(DATA_DIR) / "sessions"
            storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📂 Используется FileStorage: {storage_dir}")
            return FileStorage(base_path=str(storage_dir), format="json")

        else:
            logger.warning(
                "⚠️ Redis и FileStorage отключены, используется MemoryStorage"
            )
            return MemoryStorage()

    except (RedisError, OSError) as ex:
        logger.warning(
            f"❌ Ошибка инициализации хранилища: {ex}, fallback на MemoryStorage"
        )
        return MemoryStorage()


def atomic_write(
    self,
    path: Path,
    data: Any,
    *,
    serializer: Callable[[Any, Any], None],
    mode: Literal["text", "binary"] = "binary",
    encoding: str = "utf-8",
    suffix: str = ".tmp",
) -> None:
    """
    Atomically write data to a file using a given serializer.

    :param path: Target path to write to.
    :param data: Data to serialize and write.
    :param serializer: Callable (data, file_obj) -> None.
    :param mode: 'text' or 'binary' mode.
    :param encoding: Encoding used for text mode.
    :param suffix: Suffix for temp file.
    """
    tmp_path = None
    try:
        open_mode = "w" if mode == "text" else "wb"
        with tempfile.NamedTemporaryFile(
            mode=open_mode,
            encoding=encoding if mode == "text" else None,
            delete=False,
            dir=path.parent,
            suffix=suffix,
        ) as tmp:
            serializer(data, tmp)
            tmp_path = Path(tmp.name)

        os.replace(tmp_path, path)
        self.logger.debug(f"📝 Atomic write succeeded for {path}")

    except Exception as e:
        self.logger.error(f"❌ Atomic write failed for {path}: {e}")
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def detect_project_namespace(plugin_dir: Path) -> Optional[str]:
    """
    Автоматически определяет базовый namespace (например: 'tgnms.plugins.core')
    на основе структуры проекта и расположения plugin_dir.
    """
    try:
        root = Path.cwd().resolve()
        plugin_dir = plugin_dir.resolve()

        # Пример: /app/src/tgnms/plugins/core → tgnms.plugins.core
        common = os.path.commonpath([str(root), str(plugin_dir)])
        relative_parts = plugin_dir.relative_to(common).parts

        # Ищем часть, с которой начинается valid package (где есть __init__.py)
        candidate = []
        for part in reversed(relative_parts):
            candidate.insert(0, part)
            probe_path = root.joinpath(*candidate)
            if not probe_path.joinpath("__init__.py").exists():
                break

        namespace_parts = plugin_dir.relative_to(root).parts
        return ".".join(namespace_parts)
    except Exception as e:
        print(f"[NamespaceDetect] ⚠️ Не удалось определить namespace: {e}")
        return None


def to_string(value, encoding="utf-8"):
    """
    Преобразует значение типа OctetString, bytes или hex-строку в обычную строку.
    Если значение уже является строкой, возвращает его без изменений.
    """
    if isinstance(value, (Counter32, OctetString)):
        return value.prettyPrint()  # возвращает строковое значение
    # Преобразуем значение из OctetString в строку
    if isinstance(value, OctetString):
        # Получаем строковое представление из OctetString
        value = value.prettyPrint().encode("latin1").decode(encoding)
    # Преобразуем значение из bytes в строку
    elif isinstance(value, bytes):
        value = value.decode(encoding)
    # Проверяем, является ли строка шестнадцатеричной после преобразования
    if isinstance(value, str):
        if is_hex_string(value):
            try:
                # Если строка в hex-формате, преобразуем её в текст
                if value.startswith("0x"):
                    value = value[2:]
                value = bytes.fromhex(value).decode(encoding)
            except (ValueError, UnicodeDecodeError) as e:
                logger.error(
                    f"[{inspect.currentframe().f_code.co_name}] Ошибка при декодировании hex: {e}"
                )
                # Оставляем исходное значение и логируем ошибку, если декодировать не удалось
                pass

    return value  # Возвращаем преобразованное значение или исходное, если оно не требует изменений


def is_hex_string(s: str) -> bool:
    """
    Проверяет, является ли строка шестнадцатеричным значением.
    """
    # Убираем префикс "0x" в начале, если он есть
    if s.startswith("0x"):
        s = s[2:]

    # Проверяем, что строка состоит только из hex-символов и имеет чётную длину
    if len(s) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in s):
        try:
            # Пробуем декодировать строку как hex
            bytes.fromhex(s)
            return True
        except ValueError:
            return False
    return False


def seconds_to_str(uptime) -> str:
    """
    Преобразует значение TimeTicks или timedelta в строку в формате 'годы месяцы недели дни часы минуты секунды'.
    """
    # Проверка типа uptime и преобразование в секунды
    if isinstance(uptime, TimeTicks):
        total_seconds = int(uptime) / 100  # Преобразование TimeTicks в секунды
    elif isinstance(uptime, datetime.timedelta):
        total_seconds = int(
            uptime.total_seconds()
        )  # Преобразование timedelta в секунды
    else:
        total_seconds = int(uptime)  # Если uptime уже в секундах

    # Определяем величины времени
    seconds_in_year = 31536000  # 365 дней
    seconds_in_month = 2592000  # 30 дней
    seconds_in_week = 604800  # 7 дней
    seconds_in_day = 86400
    seconds_in_hour = 3600
    seconds_in_minute = 60

    # Вычисляем годы, месяцы, недели, дни, часы, минуты, секунды
    years = int(total_seconds // seconds_in_year)
    total_seconds %= seconds_in_year
    months = int(total_seconds // seconds_in_month)
    total_seconds %= seconds_in_month
    weeks = int(total_seconds // seconds_in_week)
    total_seconds %= seconds_in_week
    days = int(total_seconds // seconds_in_day)
    total_seconds %= seconds_in_day
    hours = int(total_seconds // seconds_in_hour)
    total_seconds %= seconds_in_hour
    minutes = int(total_seconds // seconds_in_minute)
    seconds = int(total_seconds % seconds_in_minute)

    # Формируем строку с результатом, добавляя только непустые значения
    result = []
    if years > 0:
        result.append(
            f"{years} {'год' if years == 1 else 'лет' if years >= 5 else 'года'}"
        )
    if months > 0:
        result.append(
            f"{months} {'месяц' if months == 1 else 'месяцев' if months >= 5 else 'месяца'}"
        )
    if weeks > 0:
        result.append(
            f"{weeks} {'неделя' if weeks == 1 else 'недель' if weeks >= 5 else 'недели'}"
        )
    if days > 0:
        result.append(
            f"{days} {'день' if days == 1 else 'дней' if days >= 5 else 'дня'}"
        )
    if hours > 0:
        result.append(f"{hours:02} часов")
    if minutes > 0:
        result.append(f"{minutes:02} минут")
    result.append(f"{seconds:02} секунд")  # Секунды всегда отображаются

    return " ".join(result)


def parse_location(byte_string: bytes) -> Optional[Dict[str, str]]:
    try:
        if isinstance(byte_string, bytes):
            decoded_string = byte_string.decode("utf-8")
        else:
            decoded_string = str(byte_string)
        logger.debug(
            f"[{inspect.currentframe().f_code.co_name}] RAW STRING: {decoded_string}"
        )  # Вывод для отладки

        # Используем регулярное выражение для разделения адреса и координат
        match = re.match(r"(.*)\[(.*?)\]$", decoded_string)
        if match:
            address = match.group(1).strip()
            coordinates = match.group(2).strip()
        else:
            address = decoded_string.strip()
            coordinates = None

        # Парсим адрес
        address_parts = address.split(",")
        address_parts = [part.strip() for part in address_parts if part.strip()]

        street = address_parts[0] if len(address_parts) > 0 else ""
        house_number = address_parts[1] if len(address_parts) > 1 else ""
        city = address_parts[2] if len(address_parts) > 2 else ""
        country = address_parts[3] if len(address_parts) > 3 else ""

        latitude = longitude = None
        if coordinates and "," in coordinates:
            try:
                latitude, longitude = map(float, coordinates.split(","))
            except ValueError:
                logger.error(
                    f"[{inspect.currentframe().f_code.co_name}] Invalid coordinates format"
                )
                return None

        return {
            "street": street,
            "house_number": house_number,
            "city": city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
        }
    except Exception as e:
        # Логируем ошибку
        logger.error(
            f"[{inspect.currentframe().f_code.co_name}] Error parsing location: {e}"
        )
        return None
