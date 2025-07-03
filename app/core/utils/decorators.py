from functools import wraps
from typing import Any, Callable, Coroutine, List, Optional, Union
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
from datetime import datetime

from app.core.config import logger


# ──────────────────────────────────────────────────────────────
# 1. Decorator for Safe Message Deletion
# ──────────────────────────────────────────────────────────────


def safe_delete_message(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
    """
    Decorator to safely delete a Telegram message before executing the handler.

    Logs any errors through `logger.debug` without interrupting the main execution.

    Args:
        func (Callable): Asynchronous handler function accepting a `Message` object.

    Returns:
        Callable: Wrapped asynchronous function with safe message deletion.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        from aiogram.types import Message

        message = None
        # Сначала ищем в kwargs
        for v in kwargs.values():
            if isinstance(v, Message):
                message = v
                break
            # Проверяем наличие атрибута message
            if hasattr(v, "message") and isinstance(getattr(v, "message"), Message):
                message = getattr(v, "message")
                break
        # Если не нашли, ищем в args
        if message is None:
            for v in args:
                if isinstance(v, Message):
                    message = v
                    break
                if hasattr(v, "message") and isinstance(getattr(v, "message"), Message):
                    message = getattr(v, "message")
                    break
        if isinstance(message, Message):
            try:
                await message.delete()
            except Exception as e:
                logger.debug(f"[safe_delete_message] ⚠️ Failed to delete message: {e}")
        else:
            logger.warning(
                f"[safe_delete_message] Не найден объект Message среди аргументов: {args}, {kwargs}"
            )

        return await func(*args, **kwargs)

    return wrapper


# ──────────────────────────────────────────────────────────────
# 2. Function to Send Message and Set FSM State
# ──────────────────────────────────────────────────────────────


async def send_and_set(
    message: Message,
    state: FSMContext,
    text: str,
    next_state: Any,
    keyboard: Optional[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]] = None,
) -> None:
    """
    Sends a message to the user and sets a new FSM state, preserving the UI.

    Adds a timestamp, hides the keyboard (if not specified), and calls
    `StateManager.set_state_with_previous` with display context.

    Args:
        message (Message): The original message from the user.
        state (FSMContext): The current FSM context.
        text (str): The main text to display to the user.
        next_state (State): The next FSM state (any compatible structure).
        keyboard (ReplyKeyboardMarkup | InlineKeyboardMarkup | None, optional):
            Keyboard for the message. Defaults to removing the keyboard (`ReplyKeyboardRemove`).
    """
    from app.bot.fsm.state_manager import StateManager  # Local import

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    footer = f"\n<pre><i>Completed: <code>{current_date}</code></i></pre>"
    formatted_text = text.strip() + footer

    await message.answer(
        text=formatted_text,
        reply_markup=keyboard if keyboard else ReplyKeyboardRemove(),
        parse_mode="HTML",
    )

    await StateManager.set_state_with_history(
        state,
        next_state,
        display_data={
            "text": formatted_text,
            "reply_markup": keyboard,
        },
    )


# ──────────────────────────────────────────────────────────────
# 3. Function to Chunk Buttons
# ──────────────────────────────────────────────────────────────


def chunk_buttons(
    buttons: List[KeyboardButton], chunk_size: int = 2
) -> List[List[KeyboardButton]]:
    """
    Splits a list of Telegram buttons into rows of a fixed length.

    Args:
        buttons (List[KeyboardButton]): List of flat buttons.
        chunk_size (int, optional): Maximum buttons per row. Defaults to 2.

    Returns:
        List[List[KeyboardButton]]: Nested list of button rows.
    """
    return [buttons[i : i + chunk_size] for i in range(0, len(buttons), chunk_size)]


# ──────────────────────────────────────────────────────────────
# 4. Function to Add Buttons to Section
# ──────────────────────────────────────────────────────────────


def add_buttons_to_section(
    sections: dict[str, List[List[KeyboardButton]]],
    section_name: str,
    buttons: List[KeyboardButton],
    max_per_row: int = 2,
) -> None:
    """
    Adds buttons to a specific section, splitting them into rows.

    If the section already has one row with space, it fills that row.
    Remaining buttons go into new rows.

    Args:
        sections (dict[str, List[List[KeyboardButton]]]):
            Dictionary of sections containing button rows.
        section_name (str): Name of the section.
        buttons (List[KeyboardButton]): List of buttons to add.
        max_per_row (int, optional): Maximum buttons per row. Defaults to 2.
    """
    if section_name not in sections:
        sections[section_name] = []

    chunked_buttons = chunk_buttons(buttons, max_per_row)

    # If the section has exactly one row and it has space, fill it
    if (
        len(sections[section_name]) == 1
        and len(sections[section_name][0]) < max_per_row
    ):
        first_row = sections[section_name][0]
        space_left = max_per_row - len(first_row)

        # How many buttons can be added to the first row
        to_add_first_row = chunked_buttons[0][:space_left]
        first_row.extend(to_add_first_row)

        # Remaining buttons go into new rows
        rest_buttons = chunked_buttons[0][space_left:] + sum(chunked_buttons[1:], [])
        if rest_buttons:
            sections[section_name].extend(chunk_buttons(rest_buttons, max_per_row))
    else:
        # Simply add all buttons as new rows
        sections[section_name].extend(chunked_buttons)


# ──────────────────────────────────────────────────────────────
# 5. Decorator to Handle Network Errors
# ──────────────────────────────────────────────────────────────


def handle_network_error(default_return: Any = None) -> Callable[..., Coroutine]:
    """
    Decorator to protect asynchronous network operations from failures.

    Logs exceptions as `logger.exception(...)` and returns a fallback value.

    Args:
        default_return (Any, optional): Default value to return on exception.

    Returns:
        Callable: Wrapper around the asynchronous function.
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
