from aiogram import F, Router
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from bot.constants.menu_labels import MenuLabels
from bot.utils.state_manager import StateManager
from bot.constants.states import EditProfileStates, ProfileCommands
from bot.database.user_service import get_user_by_tg_id, update_user
from aiogram.types.callback_query import CallbackQuery
from bot.keyboards.main_menu import generate_edit_choice_buttons

router = Router()

# Функция для генерации карточки профиля
def generate_profile_card(user_data):
    profile_text = (
        f"👤 <b>Профиль пользователя {user_data['tg_id']}(@{user_data['username']})</b>\n\n"

        f"👨‍💼 Имя: {user_data['first_name']} {user_data['last_name']}\n"
        f"🏢 Должность: {user_data['company_post']}\n"
        f"📱 Телефон: {user_data['phone_number']}\n"
        f"📧 Email: {user_data['email']}\n"
        f"💼 Станция: {user_data['station']}\n"
        f"{'🛡️ — Верифицирован' if user_data['is_verified'] else '🚫 — Не верифицирован'}\n"
        f"{'🅰️ — Администратор' if user_data['is_admin'] else '👤 — Пользователь'}\n"
        f"{'🔓 — Доступ открыт' if user_data['is_allowed'] else '⛔ — Доступ заблокирован'}\n"
    )

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="profile_refresh")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="profile_edit")],
    ])

    return profile_text, buttons

# Обработчик команды "Расширенное меню"
@router.message(F.text == MenuLabels.USER_PROFILE.value)
async def profile_menu_command(message: Message, state: FSMContext):
    user = await get_user_by_tg_id(message.from_user.id)

    if not user:
        await message.answer("❌ Пользователь не найден в базе данных.")
        return

    profile_text, buttons = generate_profile_card(user)

    await StateManager.set_state_with_previous(state, ProfileCommands.PROFILE, {"text": profile_text})
    await message.answer(profile_text, reply_markup=buttons)


# Обработчик кнопки "Обновить"
@router.callback_query(F.data == "profile_refresh")
async def refresh_profile(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_tg_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text("❌ Пользователь не найден в базе данных.")
        return

    profile_text, buttons = generate_profile_card(user)

    await StateManager.set_state_with_previous(state, ProfileCommands.PROFILE, {"text": profile_text})
    await callback.message.edit_text(profile_text, reply_markup=buttons)

    
# Обработчик кнопки "Редактировать"
@router.callback_query(F.data == "profile_edit")
async def edit_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ Выберите, что вы хотите изменить:",
        reply_markup=generate_edit_choice_buttons()
    )
    await state.set_state(EditProfileStates.choosing_field)

# Обработчик выбора поля для редактирования
@router.callback_query(EditProfileStates.choosing_field)
async def choose_field_to_edit(callback: CallbackQuery, state: FSMContext):
    field_map = {
        "edit_first_name": "first_name",
        "edit_last_name": "last_name",
        "edit_company_post": "company_post",
        "edit_phone_number": "phone_number",
        "edit_email": "email"
    }
    chosen_field = field_map.get(callback.data)

    if chosen_field:
        await state.update_data(chosen_field=chosen_field)
        field_name = {
            "first_name": "имя",
            "last_name": "фамилию",
            "company_post": "должность",
            "phone_number": "номер телефона",
            "email": "email"
        }.get(chosen_field)
        await callback.message.edit_text(
            f"Введите новое значение для поля <b>{field_name}</b>:",
            reply_markup=None
        )
        await state.set_state(EditProfileStates.waiting_for_new_value)
    elif callback.data == "profile_back":
        await back_to_profile(callback, state)

# Обработчик ввода нового значения
@router.message(EditProfileStates.waiting_for_new_value)
async def set_new_value(message: Message, state: FSMContext):
    user_data = await state.get_data()
    chosen_field = user_data.get("chosen_field")

    if not chosen_field:
        await message.answer("Ошибка: не выбрано поле для изменения.")
        await state.clear()
        return

    # Обновляем профиль в базе данных
    user_id = message.from_user.id
    await update_user(user_id, {chosen_field: message.text})

    # Сообщаем об успешном обновлении
    await message.answer(
        f"✅ Поле успешно обновлено!\n\nВернитесь в профиль, чтобы увидеть изменения.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в профиль", callback_data="profile_back")]
        ])
    )
    await state.clear()

# Возврат в профиль
@router.callback_query(F.data == "profile_back")
async def back_to_profile(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_tg_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text("❌ Пользователь не найден в базе данных.")
        return

    profile_text, buttons = generate_profile_card(user)
    await callback.message.edit_text(profile_text, reply_markup=buttons)