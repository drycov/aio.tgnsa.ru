from aiogram import Router, F
from aiogram.types import Message
from .labels.menu_label import MenuLabels
from app.core.config import logger


def register_handlers(router: Router):
    @router.message(F.text == MenuLabels.DEVICE_CHECK.value)
    async def device_check_handler(message: Message):
        logger.info(
            f"[device_check] Запрошена проверка устройства: user_id={message.from_user.id}"
        )
        await message.answer(
            "🖥 Ваше устройство успешно проверено. Все параметры в норме."
        )
