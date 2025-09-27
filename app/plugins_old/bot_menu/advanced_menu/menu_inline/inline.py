from aiogram import Router, F
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


def register_inline_query(router: Router):
    @router.inline_query(F.query.lower().startswith("device"))
    async def inline_check_device(query: InlineQuery):
        logger.debug(f"[InlineQuery] Received query: {query.query}")

        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="🧪 Проверка устройства",
                description="Выполнить проверку статуса устройства",
                input_message_content=InputTextMessageContent(
                    message_text="🧪 Проверка устройства... Ожидайте результат."
                ),
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="🌐 Порты устройства",
                description="Получить информацию о статусе портов",
                input_message_content=InputTextMessageContent(
                    message_text="🌐 Информация о портах будет собрана..."
                ),
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="🔗 LLDP информация",
                description="Соседи устройства по LLDP",
                input_message_content=InputTextMessageContent(
                    message_text="🔗 Получение LLDP информации..."
                ),
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="📏 Измерение кабеля",
                description="Запустить диагностику кабеля",
                input_message_content=InputTextMessageContent(
                    message_text="📏 Выполняется измерение длины кабеля..."
                ),
            ),
        ]

        await query.answer(
            results,
            cache_time=5,   # немного кэшируем
            is_personal=True
        )
