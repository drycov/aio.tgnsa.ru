import time
from logging import Logger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.core.utils.logger_manager import LoggerManager

try:
    from prometheus_client import Histogram
    REQUEST_LATENCY = Histogram(
        "tg_event_latency_seconds",
        "Latency of Telegram events",
        ["event_type"]
    )
except ImportError:
    REQUEST_LATENCY = None


class ProfilerMiddleware(BaseMiddleware):
    """
    Middleware для профилирования времени обработки событий Telegram-бота.
    Поддерживает логирование и (опционально) метрики Prometheus.
    """

    def __init__(
        self,
        logger: Logger | LoggerManager,
        warn_threshold: float = 1.0,
        enable_prometheus: bool = False,
    ):
        """
        :param logger: Экземпляр логгера или LoggerManager
        :param warn_threshold: Порог в секундах, после которого лог пишется как warning
        :param enable_prometheus: Включить экспорт метрик в Prometheus
        """
        self.logger = logger
        self.warn_threshold = warn_threshold
        self.enable_prometheus = enable_prometheus

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_type = type(event).__name__
        start = time.perf_counter()

        try:
            result = await handler(event, data)
        finally:
            duration = time.perf_counter() - start
            user_id, chat_id = self._extract_ids(event)

            msg = (
                f"⏱ {event_type:<18} | "
                f"{duration:.3f} сек. | "
                f"user_id={user_id or '-'} chat_id={chat_id or '-'}"
            )

            logger: Logger | LoggerManager | None = data.get("logger", self.logger)

            if duration >= self.warn_threshold:
                # 🐌 Медленные события выделяем
                getattr(logger, "warning", self.logger.warning)(f"🐌 {msg}")
            else:
                # ⚡ Быстрые события в отладку
                getattr(logger, "debug", self.logger.debug)(f"⚡ {msg}")

            # Метрики в Prometheus
            if self.enable_prometheus and REQUEST_LATENCY:
                REQUEST_LATENCY.labels(event_type).observe(duration)

        return result

    @staticmethod
    def _extract_ids(event: TelegramObject) -> tuple[Any, Any]:
        """Попытка извлечь user_id и chat_id из разных типов событий."""
        user_id = chat_id = None

        if isinstance(event, Message):
            user_id = getattr(event.from_user, "id", None)
            chat_id = getattr(event.chat, "id", None)
        elif isinstance(event, CallbackQuery):
            user_id = getattr(event.from_user, "id", None)
            chat_id = getattr(getattr(event.message, "chat", None), "id", None)
        elif hasattr(event, "from_user"):  # inline_query, chosen_inline_result и т.п.
            user_id = getattr(event.from_user, "id", None)
            chat_id = getattr(getattr(event, "chat", None), "id", None)

        return user_id, chat_id
