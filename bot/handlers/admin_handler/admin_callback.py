import uuid

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, FSInputFile
from tabulate import tabulate

from bot.bot_instance import bot
from bot.constants import Messages
from bot.constants.states import MainCommands, RegistrationForm
from bot.keyboards import on_enter_keyboard
from bot.models import User
from bot.utils import JWTManager
from bot.utils import StateManager, HelperFunctions
from bot.utils.logger_instance import app_logger
from config import Config
from healthy import Healthy
from logging_config import LoggingConfig

router = Router()
health_checker = Healthy()

@router.callback_query(lambda c: c.data == "approve_user")
async def approve_user(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработка подтверждения данных пользователя.
    """
    await callback_query.answer("Ваши данные подтверждены!")
    app_logger.info(f"Пользователь {callback_query.from_user.id} подтвердил свои данные.")

    user_data = await state.get_data()
    verification_code = User.generate_verification_code()
    user_hash = User.generate_hash(verification_code)
    
    try:
        # Создание нового пользователя
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
            hash=user_hash,
            api_token=JWTManager.generate_jwt(
                user_id=callback_query.from_user.id,
                secret_key=Config.SECRET_KEY,
                expires_in=64800
            ),
            uid=str(uuid.uuid4())
        )

        # Формирование сообщения для администратора
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
        admin_message = f"Новый пользователь ожидает подтверждения:\n\n{tabulate(table_data, tablefmt='plain')}"

        # Сохранение пользователя в БД
        User.create(new_user.model_dump())
        await callback_query.message.answer(
            Messages.USER_SAVED_IN_DB.value,
            reply_markup=on_enter_keyboard,
            parse_mode="HTML"
        )

        # Отправка сообщения администратору
        admin_id = Config.DEFAULT_ADMIN_ID
        if admin_id:
            await bot.send_message(admin_id, admin_message, parse_mode="HTML")
        else:
            app_logger.error("DEFAULT_ADMIN_ID не задан в конфигурации.")
            await callback_query.answer(Messages.ERROR_GENERAL.value, parse_mode="HTML")

    except Exception as e:
        app_logger.error(f"Ошибка при создании пользователя с tg_id {callback_query.from_user.id}: {e}")
        await callback_query.answer(Messages.ERROR_GENERAL.value, parse_mode="HTML")

    await state.clear()
    await state.set_state(MainCommands.START)

@router.callback_query(lambda c: c.data == "reject_user")
async def reject_user(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработка отклонения данных пользователя.
    """
    await callback_query.answer("Пожалуйста, повторите ввод данных.")
    app_logger.info(f"Пользователь {callback_query.from_user.id} отклонил свои данные.")
    
    await callback_query.message.edit_text("Ваши данные отклонены. Пожалуйста, начните регистрацию заново.")
    await StateManager.set_state_with_previous(state, RegistrationForm.first_name)
    await bot.send_message(
        callback_query.from_user.id,
        Messages.REGISTER_FIRST_NAME.value,
        reply_markup=ReplyKeyboardRemove()
    )
