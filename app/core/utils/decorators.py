from functools import wraps
from typing import Any, Callable, Coroutine, List
from aiogram.types import Message, ReplyKeyboardRemove, KeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime

from app.core.config import logger


def safe_delete_message(func):
    """
    Декоратор для безопасного удаления сообщения Telegram перед выполнением хендлера.

    При ошибке логирует её через `logger.debug`, не прерывая основное выполнение.

    Args:
        func (Callable): Асинхронная функция-хендлер, принимающая объект `Message`.

    Returns:
        Callable: Обёрнутая асинхронная функция с защитой удаления сообщения.
    """

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


async def send_and_set(
    message: Message, state: FSMContext, text: str, next_state, keyboard=None
):
    """
    Отправляет сообщение пользователю и устанавливает новое состояние FSM, сохраняя UI.

    Добавляет временную метку, скрывает клавиатуру (если не указана) и вызывает
    `StateManager.set_state_with_previous` с display-контекстом.

    Args:
        message (Message): Исходное сообщение от пользователя.
        state (FSMContext): Контекст текущего FSM.
        text (str): Основной текст для отображения пользователю.
        next_state (State): Следующее состояние FSM (любая совместимая структура).
        keyboard (ReplyKeyboardMarkup | InlineKeyboardMarkup | None, optional):
            Клавиатура для сообщения. По умолчанию удаляется клавиатура (`ReplyKeyboardRemove`).

    Returns:
        None
    """
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
    Делит список Telegram-кнопок на строки фиксированной длины.

    Args:
        buttons (List[KeyboardButton]): Список плоских кнопок.
        chunk_size (int, optional): Максимум кнопок в строке. По умолчанию 2.

    Returns:
        List[List[KeyboardButton]]: Вложенный список строк с кнопками.
    """
    return [buttons[i : i + chunk_size] for i in range(0, len(buttons), chunk_size)]


def add_buttons_to_section(
    sections: dict[str, list[list[KeyboardButton]]],
    section_name: str,
    buttons: list[KeyboardButton],
    max_per_row: int = 2,
) -> None:
    """
    Добавляет кнопки в определённую секцию с разбиением по строкам.

    Если в секции уже есть одна строка с местом — добавляет туда.
    Остальные кнопки переходят в новые строки.

    Args:
        sections (dict[str, list[list[KeyboardButton]]]):
            Словарь секций, содержащих строки кнопок.
        section_name (str): Название секции.
        buttons (list[KeyboardButton]): Список кнопок для добавления.
        max_per_row (int, optional): Максимум кнопок в одной строке. По умолчанию 2.

    Returns:
        None
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


def handle_network_error(default_return: Any = None):
    """
    Декоратор для защиты асинхронных сетевых операций от сбоев.

    Логирует исключения как `logger.exception(...)` и возвращает fallback-значение.

    Args:
        default_return (Any, optional): Значение по умолчанию при возникновении исключения.

    Returns:
        Callable: Обёртка вокруг асинхронной функции.
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
