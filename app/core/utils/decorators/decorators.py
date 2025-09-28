import logging
import traceback
import inspect
import json
from functools import wraps
from typing import Any, Callable, Coroutine, Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 1. Safe delete Telegram message
# ─────────────────────────────────────────────
def safe_delete_message(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
    """
    Декоратор: безопасно удаляет Telegram-сообщение перед вызовом хендлера.
    Не прерывает выполнение, если удаление не удалось.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from aiogram.types import Message

        message = None
        for v in list(kwargs.values()) + list(args):
            if isinstance(v, Message):
                message = v
                break
            if hasattr(v, "message") and isinstance(getattr(v, "message"), Message):
                message = getattr(v, "message")
                break

        if message:
            try:
                await message.delete()
            except Exception as e:
                logger.debug(f"[safe_delete_message] ⚠ Не удалось удалить сообщение: {e}")

        return await func(*args, **kwargs)

    return wrapper


# ─────────────────────────────────────────────
# 2. Handle network errors
# ─────────────────────────────────────────────
def handle_network_error(default_return: Any = None) -> Callable[..., Coroutine]:
    """
    Декоратор для безопасных сетевых операций.
    Логирует ошибку и возвращает default_return вместо падения.
    """
    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"[NetworkError] {func.__name__} failed", exc_info=e)
                return default_return
        return wrapper
    return decorator


# ─────────────────────────────────────────────
# 3. Execution logger (sync/async)
# ─────────────────────────────────────────────
def log_execution(
    level: str = "info",
    success_message: str = "Успешно выполнено",
    error_message: str = "Ошибка выполнения",
    log_args: bool = False,
    log_exceptions: bool = True,
    log_traceback: bool = False,
    custom_logger: Optional[logging.Logger] = None,
):
    """
    Декоратор для логирования выполнения функций.

    Поддерживает как синхронные, так и асинхронные функции.
    """
    def decorator(func: Callable):
        log = custom_logger or logging.getLogger(func.__module__)
        log_func = getattr(log, level.lower(), log.info)

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                    if log_args:
                        log_func(f"[{func.__name__}] {success_message} | args={args}, kwargs={kwargs}")
                    else:
                        log_func(f"[{func.__name__}] {success_message}")
                    return result
                except Exception as ex:
                    if log_exceptions:
                        msg = f"[{func.__name__}] {error_message}: {ex}"
                        if log_traceback:
                            msg += "\n" + traceback.format_exc()
                        log.error(msg)
                    raise
            return async_wrapper

        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    if log_args:
                        log_func(f"[{func.__name__}] {success_message} | args={args}, kwargs={kwargs}")
                    else:
                        log_func(f"[{func.__name__}] {success_message}")
                    return result
                except Exception as ex:
                    if log_exceptions:
                        msg = f"[{func.__name__}] {error_message}: {ex}"
                        if log_traceback:
                            msg += "\n" + traceback.format_exc()
                        log.error(msg)
                    raise
            return sync_wrapper

    return decorator


# ─────────────────────────────────────────────
# 4. Log model initialization (Pydantic)
# ─────────────────────────────────────────────
def log_model_init(cls):
    """
    Декоратор-класс для логирования инициализации Pydantic-моделей.
    Скрывает секретные значения (SecretStr) и сериализует в JSON.
    """
    orig_init = cls.__init__
    from rich import print

    def safe_model_dump(instance: BaseSettings) -> dict:
        def safe_val(val: Any):
            if isinstance(val, SecretStr):
                return "********"
            elif isinstance(val, set):
                return list(val)
            elif isinstance(val, BaseSettings):
                return safe_model_dump(val)
            elif isinstance(val, dict):
                return {k: safe_val(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [safe_val(i) for i in val]
            return val

        try:
            return {k: safe_val(v) for k, v in instance.model_dump().items()}
        except Exception:
            return {"error": "⚠ model_dump() failed"}

    def new_init(self, **kwargs):
        orig_init(self, **kwargs)
        try:
            dumped = json.dumps(safe_model_dump(self), indent=2, ensure_ascii=False)
        except Exception as e:
            dumped = f"[Ошибка сериализации]: {e}"

        print(f"[🔧 Init] {cls.__name__}:\n{dumped}")
        logger.debug(f"[🔧 Init] {cls.__name__}:\n{dumped}")

    cls.__init__ = new_init
    return cls
