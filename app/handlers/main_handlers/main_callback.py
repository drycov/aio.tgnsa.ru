from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.constants import MenuLabels
from app.constants.states import ALL_STATES
from app.utils import StateManager, CalendarMarkup

router = Router()


@router.message(F.text == MenuLabels.BACK.value)  # Обработчик для текстовой команды "Назад"
async def back_command_text(message: Message, state: FSMContext):
    await StateManager.handle_back_action(state, message)


@router.callback_query(F.data == "back")  # Обработчик для callback_query с данными "back"
async def back_command_callback(callback_query: CallbackQuery, state: FSMContext):
    await StateManager.handle_back_action(state, callback_query.message)
    await callback_query.answer()  # Закрывает окно callback


# Обработчик для команды /cancel, который отменяет текущее состояние
@router.callback_query(F.data == "cancel", StateFilter(*ALL_STATES))  # Обработчик для callback_query с данными "back"
async def cancel_command_callback(callback_query: CallbackQuery, state: FSMContext):
    await StateManager.handle_back_action(state, callback_query.message)

    # Удаляем предыдущее сообщение пользователя (если это нужно по логике)
    await callback_query.delete()
    await state.clear()


# Обработчик для навигации по месяцам
@router.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
async def navigate_month(callback_query: CallbackQuery):
    _, year, month = callback_query.data.split("_")
    year, month = int(year), int(month)

    # Определяем направление навигации
    direction = "next" if "next_" in callback_query.data else "prev"

    # Создаем объект календаря и обновляем месяц
    calendar = CalendarMarkup(year, month)
    updated_calendar = calendar.update_calendar(direction)

    # Обновляем сообщение с новым календарем
    await callback_query.message.edit_reply_markup(reply_markup=updated_calendar)
    await callback_query.answer()  # Закрываем callback-запрос
