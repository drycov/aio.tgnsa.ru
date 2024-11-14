from aiogram import types, F, Router
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import RegistrationForm, Messages
from app.keyboards import send_contact_keyboard, confirm_keyboard_inl
from app.utils import StateManager

router = Router()


# Шаг 1: Начало регистрации
async def start_registration(message: Message, state: FSMContext):
    display_data = {"text": Messages.REGISTER_FIRST_NAME.value}
    await message.answer(**display_data)
    await StateManager.set_state_with_previous(state, RegistrationForm.first_name, display_data=display_data)


# Шаг 2: Ввод имени
@router.message(RegistrationForm.first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    display_data = {"text": Messages.REGISTER_LAST_NAME.value}
    await message.answer(**display_data)
    await StateManager.set_state_with_previous(state, RegistrationForm.last_name, display_data=display_data)


# Шаг 3: Ввод фамилии
@router.message(RegistrationForm.last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    display_data = {"text": Messages.REGISTER_POSITION.value}
    await message.answer(**display_data)
    await StateManager.set_state_with_previous(state, RegistrationForm.company_post, display_data=display_data)


# Шаг 4: Ввод должности
@router.message(RegistrationForm.company_post)
async def process_company_post(message: types.Message, state: FSMContext):
    await state.update_data(company_post=message.text)
    display_data = {"text": Messages.REGISTER_PHONE.value, "reply_markup": send_contact_keyboard}
    await message.answer(**display_data)
    await StateManager.set_state_with_previous(state, RegistrationForm.phone_number, display_data=display_data)


# Шаг 5: Ввод номера телефона
@router.message(RegistrationForm.phone_number, F.contact)
async def process_phone_number(message: types.Message, state: FSMContext):
    contact = message.contact
    await state.update_data(phone_number=contact.phone_number)
    user_data = await state.get_data()
    first_name = user_data.get('first_name') or contact.first_name
    last_name = user_data.get('last_name') or contact.last_name
    await state.update_data(first_name=first_name, last_name=last_name)
    display_data = {"text": Messages.REGISTER_EMAIL.value}
    await message.answer(**display_data)
    await StateManager.set_state_with_previous(state, RegistrationForm.email, display_data=display_data)


# Шаг 6: Ввод email
@router.message(RegistrationForm.email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    user_data = await state.get_data()
    user_info = (
        f"Проверьте ваши данные:\nИмя: {user_data['first_name']}\n"
        f"Фамилия: {user_data['last_name']}\n"
        f"Должность: {user_data['company_post']}\n"
        f"Телефон: {user_data['phone_number']}\n"
        f"Email: {user_data['email']}"
    )
    display_data = {"text": user_info, "reply_markup": confirm_keyboard_inl}
    await message.answer(**display_data)
    await StateManager.set_state_with_previous(state, RegistrationForm.confirmation, )
