import time
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.core.utils.logger_manager import LoggerManager


class ProfilerMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger | LoggerManager):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_type = type(event).__name__
        start = time.perf_counter()

        result = await handler(event, data)

        duration = time.perf_counter() - start
        msg = f"⏱ {event_type}: обработка заняла {duration:.3f} сек."

        # Используем логгер из DI-контекста, если он есть
        logger: Logger | LoggerManager | None = data.get("logger")

        if hasattr(logger, "debug"):
            logger.debug(msg)
        else:
            self.logger.debug(msg)  # fallback к middleware-логгеру

        return result
