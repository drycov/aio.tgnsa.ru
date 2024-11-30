from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.constants import MenuLabels
from bot.utils.logger_instance import app_logger

router = Router()


# Команда "Назад"
@router.message(F.text == MenuLabels.BACK.value)
async def back_command(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception as e:
        app_logger.warning(f"Ошибка удаления сообщения: {e}")

    # Возвращаемся к предыдущему состоянию, используя сохраненные данные
