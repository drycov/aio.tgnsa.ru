from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.constants import Messages, MenuLabels
from bot.constants.states import MainCommands
from bot.keyboards import generate_main_keyboard, on_enter_keyboard
from bot.models import User
from bot.utils import StateManager
from bot.utils.logger_instance import app_logger
from config import Config

router = Router()


# Обработчик "Войти"
@router.message(F.text == MenuLabels.ENTER.value)
async def main_menu(message: Message, state: FSMContext):
    from bot.handlers.main_handlers.registration_handler import start_registration

    tg_id = message.from_user.id
    try:
        user = User.get_by_tg_id(tg_id)
    except Exception as e:
        app_logger.error(f"Ошибка при получении пользователя с tg_id {tg_id}: {e}")
        await message.answer("Произошла ошибка при проверке пользователя. Пожалуйста, попробуйте позже.")
        return

    # Проверка пользователя
    if user:
        if user.is_allowed_user() and user.is_verified_user():
            keyboard = generate_main_keyboard(user.is_admin_user())
            display_data = {"text": Messages.WELCOME.value, "reply_markup": keyboard}
            await StateManager.set_state_with_previous(state, MainCommands.MAIN_MENU, display_data)
            await message.answer(**display_data)
            await state.update_data(user_id=tg_id, is_online=True, token=user.generate_jwt(tg_id, Config.SECRET_KEY),
                                    is_admin=user.is_admin_user())
        else:
            display_data = {"text": Messages.ACCESS_DENIED.value, "reply_markup": on_enter_keyboard}
            await message.answer(**display_data)
    else:
        app_logger.info(f"Пользователь с tg_id {tg_id} не найден, начинаем регистрацию.")
        await message.answer(Messages.NOT_REGISTERED.value)
        await start_registration(message, state)

    # Удаление сообщения
    try:
        await message.delete()
    except Exception as e:
        app_logger.warning(f"Ошибка удаления сообщения: {e}")


# Команда "Выход"
@router.message(F.text == MenuLabels.EXIT.value)
async def exit_command(message: Message, state: FSMContext):
    # Пытаемся удалить сообщение
    try:
        await message.delete()
    except Exception as e:
        app_logger.warning(f"Ошибка удаления сообщения: {e}")

    # Отправляем прощальное сообщение и очищаем состояние
    try:
        display_data = {"text": Messages.GOODBYE.value, "reply_markup": ReplyKeyboardRemove()}
        await message.answer(**display_data)
        await state.clear()  # Полный выход из состояния
        await message.answer(Messages.PLEASE_ENTER.value, reply_markup=on_enter_keyboard)
        await state.set_state(MainCommands.START)  # Установка состояния "Главное меню"
        await state.update_data(user_id=message.from_user.id, is_online=True, is_admin=False, token="")

    except Exception as e:
        app_logger.error(f"Ошибка при выполнении команды выхода: {e}")
