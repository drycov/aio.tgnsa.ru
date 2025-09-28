from datetime import datetime
from typing import Any, List, Optional, Union
import logging
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)


async def send_and_set(
    message: Message,
    state: FSMContext,
    text: str,
    next_state: Any,
    keyboard: Optional[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]] = None,
) -> None:
    """
    Отправка сообщения и установка нового FSM состояния с сохранением истории.
    """
    from app.bot.fsm.state_manager import StateManager  # локальный импорт

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    # footer = f"\n<pre><i>Completed: <code>{current_date}</code></i></pre>"
    formatted_text = text.strip()

    await message.answer(
        text=formatted_text,
        reply_markup=keyboard if keyboard else ReplyKeyboardRemove(),
        parse_mode="HTML",
    )

    await StateManager.set_state_with_history(
        state,
        next_state,
        display_data={"text": formatted_text, "reply_markup": keyboard},
    )


def chunk_buttons(buttons: List[KeyboardButton], chunk_size: int = 2) -> List[List[KeyboardButton]]:
    """Разбивает список кнопок на строки."""
    return [buttons[i:i + chunk_size] for i in range(0, len(buttons), chunk_size)]


def add_buttons_to_section(
    sections: dict[str, List[List[KeyboardButton]]],
    section_name: str,
    buttons: List[KeyboardButton],
    max_per_row: int = 2,
) -> None:
    """Добавляет кнопки в указанный раздел клавиатуры."""
    if section_name not in sections:
        sections[section_name] = []

    chunked = chunk_buttons(buttons, max_per_row)

    if len(sections[section_name]) == 1 and len(sections[section_name][0]) < max_per_row:
        first_row = sections[section_name][0]
        space_left = max_per_row - len(first_row)

        to_add = chunked[0][:space_left]
        first_row.extend(to_add)

        rest = chunked[0][space_left:] + sum(chunked[1:], [])
        if rest:
            sections[section_name].extend(chunk_buttons(rest, max_per_row))
    else:
        sections[section_name].extend(chunked)
