from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.fsm.states.reg import RegistrationForm
from app.bot.constants.messages import REGISTER_MESSAGES  # <-- ваш словарь
from app.bot.keyboards.base import send_confirm_keyboard, send_contact_keyboard
from app.bot.fsm.state_manager import StateManager
from app.core.config import logger

router = Router()


async def send_and_set(
    message: Message,
    state: FSMContext,
    text: str,
    next_state,
    keyboard=None
):
    display_data = {"text": text}
    if keyboard:
        display_data["reply_markup"] = keyboard
    await message.answer(**display_data)
    await StateManager.set_state_with_previous(
        state,
        next_state,
        display_data=display_data
    )


# Шаг 1: начало регистрации
async def start_registration(message: Message, state: FSMContext):
    await send_and_set(
        message,
        state,
        REGISTER_MESSAGES["enter_first_name"],
        RegistrationForm.first_name
    )


@router.message(RegistrationForm.first_name)
async def process_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await send_and_set(
        message,
        state,
        REGISTER_MESSAGES["enter_last_name"],
        RegistrationForm.last_name
    )


@router.message(RegistrationForm.last_name)
async def process_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await send_and_set(
        message,
        state,
        REGISTER_MESSAGES["enter_position"],
        RegistrationForm.company_post
    )


@router.message(RegistrationForm.company_post)
async def process_company_post(message: Message, state: FSMContext):
    await state.update_data(company_post=message.text)
    await send_and_set(
        message,
        state,
        REGISTER_MESSAGES["enter_phone"],
        RegistrationForm.phone_number,
        keyboard=send_contact_keyboard
    )


@router.message(RegistrationForm.phone_number, F.contact)
async def process_phone_number(message: Message, state: FSMContext):
    contact = message.contact
    await state.update_data(phone_number=contact.phone_number)
    user_data = await state.get_data()
    await state.update_data(
        first_name=user_data.get("first_name") or contact.first_name,
        last_name=user_data.get("last_name") or contact.last_name
    )
    await send_and_set(
        message,
        state,
        REGISTER_MESSAGES["enter_email"],
        RegistrationForm.email
    )


@router.message(RegistrationForm.email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    user_data = await state.get_data()

    user_info = (
        f"Проверьте ваши данные:\n"
        f"👤 Имя: {user_data.get('first_name', '-')}\n"
        f"👥 Фамилия: {user_data.get('last_name', '-')}\n"
        f"💼 Должность: {user_data.get('company_post', '-')}\n"
        f"📞 Телефон: {user_data.get('phone_number', '-')}\n"
        f"✉️ Email: {user_data.get('email', '-')}"
    )

    await message.answer(text=user_info, reply_markup=send_confirm_keyboard)
    await StateManager.set_state_with_previous(
        state,
        RegistrationForm.confirmation,
        display_data={"text": REGISTER_MESSAGES["success"], "reply_markup": send_confirm_keyboard}
    )
