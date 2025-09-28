# app/bot/handlers/register_handlers/registration_handler.py

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, Contact
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from app.bot.fsm.states.reg import RegistrationForm
from app.bot.constants.messages import REGISTER_MESSAGES
from app.bot.constants.positions import POSITIONS_BY_DEPARTMENT, POSITIONS_BY_CODE
from app.bot.keyboards.base import (
    generate_confirm_keyboard,
    generate_department_keyboard,
    generate_position_keyboard,
    build_auth_keyboard,
    build_send_contact_keyboard,
)
from app.bot.fsm.state_manager import StateManager
from app.services.registration_buffer import RegistrationBuffer
from app.core.config import settings
from app.core.utils.decorators import send_and_set, log_execution

import logging
import re

logger = logging.getLogger(__name__)
router = Router()

# 🔑 Клавиатура входа (Enter / Exit)
on_enter_keyboard = build_auth_keyboard(False)


# 🔧 Проверка доступности чата
async def is_chat_available(bot: Bot, user_id: int) -> bool:
    try:
        await bot.get_chat(user_id)
        return True
    except (TelegramBadRequest, TelegramForbiddenError):
        return False


# Шаг 0: начало регистрации
@log_execution(level="info", success_message="Регистрация начата")
async def start_registration(message: Message, state: FSMContext):
    await send_and_set(
        message, state, REGISTER_MESSAGES["enter_first_name"], RegistrationForm.first_name
    )


# Шаг 1: Имя
@router.message(RegistrationForm.first_name)
@log_execution(success_message="Имя получено")
async def process_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())
    await send_and_set(message, state, REGISTER_MESSAGES["enter_last_name"], RegistrationForm.last_name)


# Шаг 2: Фамилия
@router.message(RegistrationForm.last_name)
@log_execution(success_message="Фамилия получена")
async def process_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await send_and_set(
        message,
        state,
        REGISTER_MESSAGES["enter_department"],
        RegistrationForm.deportament,
        keyboard=generate_department_keyboard(),
    )


# Шаг 3: Выбор направления
@router.callback_query(F.data.startswith("department:"))
@log_execution(success_message="Выбрано направление")
async def department_selected(callback: CallbackQuery, state: FSMContext):
    department = callback.data.split(":", 1)[1].strip().upper()
    dept_info = POSITIONS_BY_DEPARTMENT.get(department)
    dept_label = dept_info["label"] if dept_info else department

    await state.update_data(department=dept_label)

    await callback.message.edit_text(
        f"🏢 Направление: <b>{dept_label}</b>\n\nТеперь выберите должность:",
        reply_markup=generate_position_keyboard(department),
    )
    await callback.answer()


# Шаг 4: Выбор должности
@router.callback_query(F.data.startswith("position:"))
@log_execution(success_message="Должность выбрана")
async def position_selected(callback: CallbackQuery, state: FSMContext):
    position_code = callback.data.split(":")[1]

    # ✅ Используем словарь быстрого поиска
    pos_info = POSITIONS_BY_CODE.get(position_code)

    if not pos_info:
        await callback.message.edit_text("❌ Не удалось определить должность.")
        await callback.answer()
        return

    position_name, dept_code, dept_label = pos_info

    await state.update_data(company_post=position_name, department=dept_label)

    await callback.message.edit_text(f"✅ Должность выбрана: {position_name}")

    await callback.message.answer(
        REGISTER_MESSAGES["enter_phone"],
        reply_markup=build_send_contact_keyboard(),
    )

    await StateManager.set_state_with_history(
        state,
        RegistrationForm.phone_number,
        display_data={
            "text": REGISTER_MESSAGES["enter_phone"],
            "reply_markup": build_send_contact_keyboard(),
        },
    )

    await callback.answer()


# 🔙 Кнопка "Назад" к выбору направления
@router.callback_query(F.data == "back_to_departments")
@log_execution(success_message="Возврат к выбору направления")
async def back_to_departments(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите направление:", reply_markup=generate_department_keyboard()
    )
    await callback.answer()


# Шаг 5: Получение телефона
@router.message(RegistrationForm.phone_number, F.contact)
@log_execution(success_message="Номер телефона получен")
async def process_phone_number(message: Message, state: FSMContext):
    contact: Contact = message.contact
    await state.update_data(phone_number=contact.phone_number)

    # Дополним имя и фамилию из контакта, если их не ввели
    user_data = await state.get_data()
    await state.update_data(
        first_name=user_data.get("first_name") or contact.first_name,
        last_name=user_data.get("last_name") or contact.last_name,
    )

    await send_and_set(message, state, REGISTER_MESSAGES["enter_email"], RegistrationForm.email)


# Шаг 6: Email и подтверждение
@router.message(RegistrationForm.email)
@log_execution(success_message="Email получен")
async def process_email(message: Message, state: FSMContext):
    email = message.text.strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email, re.IGNORECASE):
        await message.answer("❌ Неверный формат email. Попробуйте ещё раз.")
        return

    await state.update_data(email=email)
    user_data = await state.get_data()

    summary = (
        f"📋 Проверьте введённые данные:\n"
        f"👤 Имя: {user_data.get('first_name', '-')}\n"
        f"👥 Фамилия: {user_data.get('last_name', '-')}\n"
        f"🏢 Направление: {user_data.get('department', '-')}\n"
        f"💼 Должность: {user_data.get('company_post', '-')}\n"
        f"📞 Телефон: {user_data.get('phone_number', '-')}\n"
        f"✉️ Email: {user_data.get('email', '-')}"
    )

    user_id = message.from_user.id
    await message.answer(summary, reply_markup=generate_confirm_keyboard("registration", user_id))

    await StateManager.set_state_with_history(
        state,
        RegistrationForm.confirmation,
        display_data={
            "text": REGISTER_MESSAGES["success"],
            "reply_markup": generate_confirm_keyboard("registration", user_id),
        },
    )


# Подтверждение регистрации
@router.callback_query(F.data.startswith("registration:confirm:"))
@log_execution(success_message="Регистрация подтверждена")
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_user_id = callback.from_user.id
    full_name = callback.from_user.full_name

    logger.info(f"[registration] Sent for approval: {user_data}")

    await state.clear()
    await callback.message.edit_text("✅ Регистрация отправлена на подтверждение.")
    await callback.message.answer("⏳ Ожидайте подтверждения от администратора...", reply_markup=on_enter_keyboard)

    # Сохраняем во временный буфер
    await RegistrationBuffer.set(current_user_id, user_data)

    # Формируем заявку
    summary = (
        f"📥 Новая заявка на регистрацию от @{callback.from_user.username or 'неизвестно'}\n"
        f"👤 Имя: {user_data.get('first_name')}\n"
        f"👥 Фамилия: {user_data.get('last_name')}\n"
        f"🏢 Отдел: {user_data.get('department')}\n"
        f"💼 Должность: {user_data.get('company_post')}\n"
        f"📞 Телефон: {user_data.get('phone_number')}\n"
        f"✉️ Email: {user_data.get('email')}\n"
        f"🆔 TG ID: <code>{current_user_id}</code>\n"
        f"🔗 Имя: {full_name}"
    )

    keyboard = generate_confirm_keyboard("admin", current_user_id)

    bot = callback.bot
    admins_reached = False

    # Отправка всем админам
    for admin_id in settings.bot.ADMINS:
        if not await is_chat_available(bot, admin_id):
            logger.warning(f"[admin_notify] Пропущен admin_id={admin_id} — бот не может отправить сообщение.")
            continue
        try:
            await bot.send_message(admin_id, summary, reply_markup=keyboard, parse_mode="HTML")
            admins_reached = True
        except Exception:
            logger.exception(f"[admin_notify] Не удалось отправить заявку админу {admin_id}")

    # Если админы недоступны → отправляем владельцу
    if not admins_reached:
        owner_id = settings.bot.owner_id
        if await is_chat_available(bot, owner_id):
            try:
                await bot.send_message(
                    owner_id,
                    f"⚠️ Ни один из админов не доступен.\nПередаём заявку владельцу:\n\n{summary}",
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
                logger.info(f"[admin_notify] Заявка передана владельцу: {owner_id}")
            except Exception:
                logger.exception(f"[owner_notify] Ошибка отправки владельцу {owner_id}")
        else:
            logger.critical("[admin_notify] Ни один админ и владелец не доступны — заявка потеряна.")

    await callback.answer()


# Отмена регистрации
@router.callback_query(F.data.startswith("registration:cancel:"))
@log_execution(success_message="Регистрация отменена")
async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Регистрация отменена.")
    await callback.message.answer("Чтобы начать заново, нажмите кнопку ниже.", reply_markup=on_enter_keyboard)


# Команда /cancel
@router.message(F.text == "/cancel")
@log_execution(success_message="Пользователь отменил регистрацию")
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Регистрация отменена.", reply_markup=on_enter_keyboard)
