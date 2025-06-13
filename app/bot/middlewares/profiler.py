import time
from logging import Logger  # <- используем правильный тип логгера
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.core.utils.logger_manager import LoggerManager


class ProfilerMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger):
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        start = time.perf_counter()
        result = await handler(event, data)
        duration = time.perf_counter() - start

        msg = f"⏱ Обработка заняла {duration:.3f} сек."

        # Безопасный доступ к логгеру из контекста
        logger: Logger | None = data.get("logger")

        if isinstance(logger, Logger):
            logger.debug(msg)
        else:
            self.logger.debug(msg)  # Fallback к основному логгеру
            # или print(msg) — если вы хотите видеть это в stdout

        return result
