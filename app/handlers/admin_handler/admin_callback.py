from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
from tabulate import tabulate

from app.bot_instance import bot
from app.constants import Messages
from app.constants.states import MainCommands, RegistrationForm
from app.keyboards import on_enter_keyboard
from app.models import User
from app.utils import StateManager
from app.utils.logger_instance import app_logger
from config import Config

router = Router()


@router.callback_query(lambda c: c.data == "approve_user")
async def approve_user(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Ваши данные подтверждены!")
    app_logger.info(f"Пользователь {callback_query.from_user.id} подтвердил свои данные.")

    # Сбор данных пользователя из состояния
    user_data = await state.get_data()
    verification_code = User.generate_verification_code()
    user_hash = User.generate_hash(verification_code)
    app_logger.info(f"Код подтверждения: {verification_code}")

    try:
        # Создаем новый объект User
        new_user = User(
            is_bot=callback_query.from_user.is_bot,
            tg_id=callback_query.from_user.id,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            company_post=user_data['company_post'],
            phone_number=user_data['phone_number'],
            username=callback_query.from_user.username or f"u{callback_query.from_user.id}",
            is_admin=False,
            is_allowed=False,
            is_verified=False,
            verification_code=verification_code,
            email=user_data['email'],
            hash=user_hash
        )

        # Данные для таблицы
        table_data = [
            ["Telegram ID", new_user.tg_id],
            ["Username", new_user.username],
            ["Полное имя", f"{new_user.first_name} {new_user.last_name}"],
            ["Должность", new_user.company_post],
            ["Phone", new_user.phone_number],
            ["E-Mail", new_user.email],
            ["Подтвердить", f"/approve_{callback_query.from_user.id}"],
            ["Отклонить", f"/reject_{callback_query.from_user.id}"]
        ]

        # Создание таблицы из данных
        table_str = tabulate(table_data, tablefmt="plain")
        admin_message = f"Новый пользователь ожидает подтверждения:\n\n{table_str}"

        # Сохранение пользователя в базу данных
        User.create(new_user.model_dump())
        await callback_query.message.answer(Messages.USER_SAVED_IN_DB.value, reply_markup=on_enter_keyboard,
                                            parse_mode="HTML")

        # Проверка наличия admin ID
        admin_id = Config.DEFAULT_ADMIN_ID
        if admin_id is None:
            app_logger.error("DEFAULT_ADMIN_ID не задан в конфигурации.")
            await callback_query.answer(Messages.ERROR_GENERAL.value, parse_mode="HTML")
            return

        # Отправка таблицы с данными пользователя администратору
        try:
            await bot.send_message(admin_id, admin_message, parse_mode="HTML")
        except Exception as send_error:
            app_logger.error(f"Ошибка при отправке сообщения администратору (chat_id={admin_id}): {send_error}")

    except Exception as e:
        app_logger.error(f"Ошибка при создании пользователя с tg_id {callback_query.from_user.id}: {e}")
        await callback_query.answer(Messages.ERROR_GENERAL.value, parse_mode="HTML")

    # Очищаем состояние после завершения регистрации
    await state.clear()
    await state.set_state(MainCommands.START)


@router.callback_query(lambda c: c.data == "reject_user")
async def reject_user(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Пожалуйста, повторите ввод данных.")
    app_logger.info(f"Пользователь {callback_query.from_user.id} отклонил свои данные.")
    await callback_query.message.edit_text("Ваши данные отклонены. Пожалуйста, начните регистрацию заново.")

    await StateManager.set_state_with_previous(state, RegistrationForm.first_name)
    await bot.send_message(callback_query.from_user.id, Messages.REGISTER_FIRST_NAME.value,
                           reply_markup=ReplyKeyboardRemove())
