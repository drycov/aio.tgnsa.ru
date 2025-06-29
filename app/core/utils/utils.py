import os
import tempfile
from typing import Any, Callable, Literal, Optional
import redis.asyncio as redis
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.exceptions import RedisError
import tomli_w

from app.bot.fsm.file_storage import FileStorage
from app.core.config import logger, settings
from app.core.config import DATA_DIR

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
