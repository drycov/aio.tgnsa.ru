from functools import wraps
from typing import Any, Callable, Coroutine, List
from aiogram.types import Message, ReplyKeyboardRemove, KeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.config import logger


def safe_delete_message(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):

        message: Message = kwargs.get("message") or (args[0] if args else None)

        if isinstance(message, Message):
            try:
                await message.delete()
            except Exception as e:
                logger.debug(f"[safe_delete_message] ⚠️ Failed to delete message: {e}")
        else:
            logger.warning(f"[safe_delete_message] Invalid message argument: {message}")

        return await func(*args, **kwargs)

    return wrapper


from datetime import datetime


async def send_and_set(
    message: Message, state: FSMContext, text: str, next_state, keyboard=None
):
    from app.bot.fsm.state_manager import StateManager  # ← локально

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    footer = f"\n<pre><i>Выполнено:  <code>{current_date}</code></i></pre>"
    formatted_text = text.strip() + footer

    await message.answer(
        text=formatted_text,
        reply_markup=keyboard if keyboard else ReplyKeyboardRemove(),
        parse_mode="HTML",
    )

    await StateManager.set_state_with_previous(
        state,
        next_state,
        display_data={
            "text": formatted_text,
            "reply_markup": keyboard,
        },
    )


def chunk_buttons(
    buttons: List[KeyboardButton], chunk_size: int = 2
) -> List[List[KeyboardButton]]:
    """
    Разбить список кнопок на вложенный список с подсписками длиной не более chunk_size.
    """
    return [buttons[i : i + chunk_size] for i in range(0, len(buttons), chunk_size)]


def add_buttons_to_section(
    sections: dict[str, list[list[KeyboardButton]]],
    section_name: str,
    buttons: list[KeyboardButton],
    max_per_row: int = 2,
) -> None:
    """
    Добавляет кнопки в указанную секцию sections.
    Если в секции уже есть ровно одна строка с < max_per_row кнопками,
    новые кнопки добавляются туда, пока не достигнем max_per_row.
    Остальные кнопки идут в новые строки с max_per_row кнопок.
    """
    if section_name not in sections:
        sections[section_name] = []

    chunked_buttons = chunk_buttons(buttons, max_per_row)

    # Если в секции ровно одна строка и в ней меньше max_per_row кнопок — дополним её
    if (
        len(sections[section_name]) == 1
        and len(sections[section_name][0]) < max_per_row
    ):
        first_row = sections[section_name][0]
        space_left = max_per_row - len(first_row)

        # Сколько кнопок можно добавить в первую строку
        to_add_first_row = chunked_buttons[0][:space_left]
        first_row.extend(to_add_first_row)

        # Оставшиеся кнопки идут в новые строки
        rest_buttons = chunked_buttons[0][space_left:] + sum(chunked_buttons[1:], [])
        if rest_buttons:
            sections[section_name].extend(chunk_buttons(rest_buttons, max_per_row))
    else:
        # Просто добавляем все кнопки как новые строки
        sections[section_name].extend(chunked_buttons)


from functools import wraps


def handle_network_error(default_return: Any = None):
    """
    Универсальный декоратор для безопасного выполнения асинхронных сетевых операций.
    При ошибке логирует и возвращает default_return.
    """

    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"[NetworkError] {func.__name__} failed: {e}")
                return default_return

        return wrapper

    return decorator
