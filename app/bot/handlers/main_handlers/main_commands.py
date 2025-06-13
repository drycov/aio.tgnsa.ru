from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from bot.keyboards import generate_main_keyboard, on_enter_keyboard

from app.bot.constants.labels import MenuLabels
from app.bot.constants.messages import Messages
from app.bot.fsm.states.main import MAINState
from app.core.config import logger

router = Router()

# Команда "Выход"


@router.message(F.text == MenuLabels.EXIT.value)
async def exit_command(message: Message, state: FSMContext):
    # Пытаемся удалить сообщение
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Ошибка удаления сообщения: {e}")

    # Отправляем прощальное сообщение и очищаем состояние
    try:
        display_data = {"text": Messages.GOODBYE.value,
                        "reply_markup": ReplyKeyboardRemove()}
        await message.answer(**display_data)
        await state.clear()  # Полный выход из состояния
        await message.answer(Messages.PLEASE_ENTER.value, reply_markup=on_enter_keyboard)
        # Установка состояния "Главное меню"
        await state.set_state(MAINState.MAIN)
        await state.update_data(user_id=message.from_user.id, is_online=True, is_admin=False, token="")

    except Exception as e:
        logger.error(f"Ошибка при выполнении команды выхода: {e}")
