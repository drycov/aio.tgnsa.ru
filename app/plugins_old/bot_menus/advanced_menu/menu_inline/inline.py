from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from uuid import uuid4


def register_inline_query(router: Router):
    @router.inline_query(F.query.lower().startswith("device"))
    async def inline_check_device(query: InlineQuery):
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Проверка устройства",
                description="Выполнить проверку статуса устройства",
                input_message_content=InputTextMessageContent(
                    message_text="🖥 Выполняется проверка устройства..."
                ),
            )
        ]
        await query.answer(results, cache_time=1, is_personal=True)
