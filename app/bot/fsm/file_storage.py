import logging
import os
import json
import yaml
import msgpack
import tomli_w
import tomllib

from typing import Optional, Dict, Any, Callable, Literal

import aiofiles
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from app.core.config import logger

# --- Поддержка сериализации ---
SerialFormat = Literal["json", "toml", "yaml", "msgpack"]
logger = logging.getLogger(__name__)


def strip_unsupported(obj):
    """
    Удаляет неподдерживаемые типы данных из вложенных структур,
    преобразуя к строке или упрощённым типам.
    """
    if isinstance(obj, dict):
        return {k: strip_unsupported(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [strip_unsupported(v) for v in obj]
    elif isinstance(obj, tuple):
        return [strip_unsupported(v) for v in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


class FileStorage(BaseStorage):
    """
    Расширяемое файловое хранилище состояний и данных FSM
    с поддержкой сериализации в JSON, TOML, YAML и MessagePack.
    """

    # ──────────────────────────────────────────────────────────────
    # 1. Инициализация и конфигурация
    # ──────────────────────────────────────────────────────────────

    def __init__(
        self,
        *,
        base_path: Optional[str] = None,
        format: SerialFormat = "json",
    ):
        """
        Создаёт экземпляр файлового хранилища FSM.

        :param base_path: Путь к директории хранения (по умолчанию ./fsm_storage)
        :param format: Формат сериализации (json, toml, yaml, msgpack)
        :param logger: Кастомный логгер (если не указан — будет создан)
        """
        self.directory = os.path.abspath(base_path or "./fsm_storage")
        self.format = format.lower()
        self.logger = logger
        self.file_ext = self._resolve_file_extension()
        self.serializer, self.deserializer = self._resolve_serializers()

        os.makedirs(self.directory, exist_ok=True)
        self.logger.debug(
            f"FileStorage initialized at {self.directory} with format '{self.format}'"
        )

    def _resolve_file_extension(self) -> str:
        """
        Возвращает расширение файла на основе формата сериализации.
        """
        return {
            "json": ".json",
            "toml": ".toml",
            "yaml": ".yaml",
            "msgpack": ".mpk",
        }.get(self.format, ".dat")

    def _resolve_serializers(
        self,
    ) -> tuple[Callable[[Any], bytes], Callable[[bytes], Any]]:
        """
        Подбирает функции сериализации и десериализации для выбранного формата.
        """
        if self.format == "json":
            return (
                lambda d: json.dumps(d).encode("utf-8"),
                lambda b: json.loads(b.decode("utf-8")),
            )
        elif self.format == "toml":
            return (
                lambda d: tomli_w.dumps(d).encode("utf-8"),
                lambda b: tomllib.loads(b.decode("utf-8")),
            )
        elif self.format == "yaml":
            return (
                lambda d: yaml.dump(d).encode("utf-8"),
                lambda b: yaml.safe_load(b.decode("utf-8")),
            )
        elif self.format == "msgpack":
            return (
                lambda d: msgpack.packb(d, use_bin_type=True),
                lambda b: msgpack.unpackb(b, raw=False),
            )
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    # ──────────────────────────────────────────────────────────────
    # 2. Работа с путями и хэшами
    # ──────────────────────────────────────────────────────────────

    def _get_file_path(self, key: StorageKey, section: Literal["state", "data"]) -> str:
        """
        Возвращает путь к файлу состояния или данных.
        Создаёт необходимые директории.
        """
        user_dir = os.path.join(self.directory, str(key.bot_id), str(key.user_id))
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, f"{section}{self.file_ext}")

    # ──────────────────────────────────────────────────────────────
    # 3. Низкоуровневая работа с файлами
    # ──────────────────────────────────────────────────────────────

    async def _read_file(self, path: str) -> dict:
        """
        Читает содержимое файла и десериализует его. В случае ошибки — сбрасывает файл.
        """
        if not os.path.exists(path):
            return {}

        try:
            async with aiofiles.open(path, "rb") as f:
                raw = await f.read()
            return self.deserializer(raw)
        except Exception as e:
            self.logger.warning(f"Corrupted file, resetting: {path} ({e})")
            await self._write_file(path, {})
            return {}

    async def _write_file(self, path: str, data: dict) -> None:
        """
        Сериализует и записывает данные в файл.
        """
        try:
            async with aiofiles.open(path, "wb") as f:
                await f.write(self.serializer(data))
        except Exception as e:
            self.logger.exception(f"Failed to write file {path}: {e}")

    # ──────────────────────────────────────────────────────────────
    # 4. Управление состоянием (FSM State)
    # ──────────────────────────────────────────────────────────────

    async def get_state(self, key: StorageKey) -> Optional[str]:
        """
        Возвращает текущее состояние FSM для заданного ключа.
        """
        path = self._get_file_path(key, "state")
        data = await self._read_file(path)
        return data.get("state")

    async def set_state(self, key: StorageKey, state: Optional[State]) -> None:
        """
        Устанавливает состояние FSM.
        """
        path = self._get_file_path(key, "state")
        file_data = await self._read_file(path)
        file_data["state"] = state.state if state else None
        await self._write_file(path, file_data)
        self.logger.debug(f"Set state for {key}: {state.state if state else None}")

    # ──────────────────────────────────────────────────────────────
    # 5. Пользовательские данные (FSM Data)
    # ──────────────────────────────────────────────────────────────

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        """
        Возвращает прикреплённые данные FSM для заданного ключа.
        """
        path = self._get_file_path(key, "data")
        try:
            async with aiofiles.open(path, "rb") as f:
                raw = await f.read()
            data = self.deserializer(raw)
            return data.get("data", {})
        except Exception as e:
            self.logger.error(f"❌ Failed to read file {path}: {e}")
            self.logger.debug(
                f"🧨 Corrupted file content:\n{raw[:300] if 'raw' in locals() else '<not loaded>'}"
            )
            return {}

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """
        Устанавливает данные пользователя FSM с предварительной фильтрацией.
        """
        path = self._get_file_path(key, "data")
        file_data = await self._read_file(path)

        safe_data = strip_unsupported(data)
        file_data["data"] = safe_data

        await self._write_file(path, file_data)
        self.logger.debug(f"Set data for {key}: {safe_data}")

    # ──────────────────────────────────────────────────────────────
    # 6. Очистка и завершение
    # ──────────────────────────────────────────────────────────────

    async def clear(self, key: StorageKey) -> None:
        """
        Удаляет файлы состояния и данных для ключа.
        Если директории становятся пустыми — они также удаляются.
        """
        try:
            state_path = self._get_file_path(key, "state")
            data_path = self._get_file_path(key, "data")

            for path in [state_path, data_path]:
                if os.path.exists(path):
                    os.remove(path)
                    self.logger.info(f"Removed: {path}")

            # Удаляем директории (user и bot), если они пустые
            user_dir = os.path.dirname(state_path)  # одинаково для обоих
            bot_dir = os.path.dirname(user_dir)
            for dir_path in [user_dir, bot_dir]:
                if os.path.isdir(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    self.logger.debug(f"Removed empty directory: {dir_path}")

        except Exception as e:
            self.logger.error(f"Failed to clear storage for {key}: {e}")

    async def clear_all(self) -> None:
        """
        Полностью очищает директорию хранилища FSM (использовать с осторожностью).
        """
        import shutil

        try:
            if os.path.exists(self.directory):
                shutil.rmtree(self.directory)
                os.makedirs(self.directory, exist_ok=True)
                self.logger.warning(
                    f"FSM storage directory fully cleared: {self.directory}"
                )
        except Exception as e:
            self.logger.exception(f"Failed to clear full storage: {e}")

    async def close(self) -> None:
        """
        Завершает работу хранилища.
        """
        await super().close()
        self.logger.debug("FileStorage closed")

    # ──────────────────────────────────────────────────────────────
    # 7. Резервный десериализатор (fallback)
    # ──────────────────────────────────────────────────────────────

    def _fallback_deserializer(self, raw: bytes) -> dict:
        """
        Альтернативная попытка десериализации при ошибке основной.
        Используется JSON как резервный формат.
        """
        try:
            return self.deserializer(raw)
        except Exception as e:
            self.logger.warning(
                f"Primary deserialization failed, fallback to JSON: {e}"
            )
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception as json_e:
                self.logger.error(f"Fallback JSON also failed: {json_e}")
                return {}
