from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.constants import MenuLabels, Messages
from app.constants.states import DeviceCommands, MainCommands
from app.keyboards import on_enter_keyboard, admin_keyboard, main_keyboard
from app.models import User
from app.utils import StateManager
from app.utils.logger_instance import app_logger

router = Router()


# Обработчик "Войти"
@router.message(F.text == MenuLabels.ENTER.value)
async def main_menu(message: Message, state: FSMContext):
    from .registration_handler import start_registration

    tg_id = message.from_user.id
    try:
        user = User.get_by_tg_id(tg_id)
    except Exception as e:
        app_logger.error(f"Ошибка при получении пользователя с tg_id {tg_id}: {e}")
        await message.answer("Произошла ошибка при проверке пользователя. Пожалуйста, попробуйте позже.")
        return

    # Проверка пользователя
    if user:
        if user.is_admin_user():
            display_data = {"text": Messages.WELCOME.value, "reply_markup": admin_keyboard}
            await StateManager.set_state_with_previous(state, MainCommands.MAIN_MENU, )
            await message.answer(**display_data)
        elif user.is_allowed_user() and user.is_verified_user():
            display_data = {"text": Messages.WELCOME.value, "reply_markup": main_keyboard}
            await StateManager.set_state_with_previous(state, MainCommands.MAIN_MENU, display_data)
            await message.answer(**display_data)
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


@router.message(F.text == MenuLabels.DEVICE_CHECK.value)
async def check_device_command(message: Message, state: FSMContext):
    display_data = {"text": "Проверка устройства начата."}
    await StateManager.set_state_with_previous(state, DeviceCommands.CHECK_STATUS, display_data)
    await message.answer(**display_data)


@router.message(F.text == MenuLabels.PORT_STATUS.value)
async def port_info_command(message: Message, state: FSMContext):
    display_data = {"text": "Получение информации о порте."}
    await StateManager.set_state_with_previous(state, DeviceCommands.PORT_INFORMATION, display_data)
    await message.answer(**display_data)


@router.message(F.text == MenuLabels.ADMIN_PANEL.value)
async def admin_panel_command(message: Message, state: FSMContext):
    display_data = {"text": "Администрирование.", "reply_markup": admin_keyboard}
    await StateManager.set_state_with_previous(state, MainCommands.ADMIN_PANEL, display_data)
    await message.answer(**display_data)


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
    except Exception as e:
        app_logger.error(f"Ошибка при выполнении команды выхода: {e}")


# Команда "Назад"
@router.message(F.text == MenuLabels.BACK.value)
async def back_command(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception as e:
        app_logger.warning(f"Ошибка удаления сообщения: {e}")

    # Возвращаемся к предыдущему состоянию, используя сохраненные данные