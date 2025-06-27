from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from typing import Optional, Dict, Any, Union, List
import logging
from enum import Enum
from dataclasses import asdict, is_dataclass

from app.bot.constants.labels import MenuLabels
from app.bot.constants.messages import Messages
from app.bot.keyboards.main import generate_main_keyboard

logger = logging.getLogger(__name__)


class MarkupType(str, Enum):
    REPLY = "reply"
    INLINE = "inline"


class StateManager:
    """
    Улучшенный FSM-менеджер с:
    - Поддержкой истории состояний
    - Сериализацией разметки
    - Кэшированием состояний
    - Оптимизированными операциями
    """

    _state_cache: Dict[str, State] = {}
    _markup_cache: Dict[str, Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]] = {}

    @classmethod
    async def set_state_with_history(
        cls,
        state: FSMContext,
        new_state: State,
        display_data: Optional[Dict[str, Any]] = None,
        action: Optional[str] = None,
        *,
        force_update: bool = False,
    ) -> None:
        current_state = await state.get_state()
        new_state_str = new_state.state if isinstance(new_state, State) else new_state

        if not force_update and current_state == new_state_str:
            return

        session_data = await state.get_data()
        display_history = session_data.get("display_history", {})
        action_history = session_data.get("action_history", {})
        state_chain = session_data.get("state_chain", [])

        # 🔐 Безопасно сериализуем reply_markup
        if (
            display_data
            and "reply_markup" in display_data
            and not isinstance(display_data["reply_markup"], (dict, str))
        ):
            display_data["reply_markup"] = cls.serialize_markup(
                display_data["reply_markup"]
            )

        if current_state:
            display_history[new_state_str] = display_data or {}
            action_history[new_state_str] = action or None
            state_chain.append(new_state_str)

        update_data = {
            "previous_state": current_state,
            "display_history": display_history,
            "action_history": action_history,
            "state_chain": state_chain,
        }

        await state.update_data(update_data)
        await state.set_state(new_state)
        cls._state_cache[new_state_str] = new_state

    @classmethod
    async def handle_back_action(cls, state: FSMContext, message: Message) -> None:
        """
        Обрабатывает действие "назад" с учетом истории состояний.

        Args:
            state: Контекст FSM
            message: Сообщение от пользователя
        """
        data = await state.get_data()
        previous_state = data.get("previous_state")
        display_history = data.get("display_history", {})
        action_history = data.get("action_history", {})

        if previous_state and action_history.get(previous_state) not in {
            "input_field",
            "input",
            None,
        }:
            await cls._restore_previous_state(
                previous_state, display_history, state, message
            )
        else:
            await cls._return_to_main_menu(data, state, message)

    @classmethod
    async def _restore_previous_state(
        cls,
        state_name: str,
        display_history: Dict[str, Any],
        state: FSMContext,
        message: Message,
    ) -> None:
        """Восстанавливает предыдущее состояние из истории."""
        display_data = display_history.get(
            state_name, {"text": "🔙 Возврат на предыдущий шаг"}
        )

        if "reply_markup" in display_data and isinstance(
            display_data["reply_markup"], dict
        ):
            display_data["reply_markup"] = cls.deserialize_markup(
                display_data["reply_markup"]
            )

        cached_state = cls._state_cache.get(state_name)
        await state.set_state(cached_state or state_name)
        await message.answer(**display_data)

    @classmethod
    async def _return_to_main_menu(
        cls, user_data: Dict[str, Any], state: FSMContext, message: Message
    ) -> None:
        """Возвращает пользователя в главное меню."""
        from app.bot.fsm.states.main import MAINState  # Ленивый импорт

        is_admin = user_data.get("is_admin", False)
        keyboard = cls._get_cached_markup(
            f"main_menu_{is_admin}", lambda: generate_main_keyboard(is_admin=is_admin)
        )

        await state.set_state(MAINState.MAIN)
        await message.answer(text=Messages.WELCOME.value, reply_markup=keyboard)

    @classmethod
    def _get_cached_markup(
        cls, cache_key: str, factory: callable
    ) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]:
        """Получает разметку из кэша или создает новую."""
        if cache_key not in cls._markup_cache:
            cls._markup_cache[cache_key] = factory()
        return cls._markup_cache[cache_key]

    @staticmethod
    def serialize_markup(
        markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup],
    ) -> Dict[str, Any]:
        """
        Сериализует разметку в словарь.

        Поддерживает:
        - ReplyKeyboardMarkup
        - InlineKeyboardMarkup
        - Любые dataclass-объекты
        """
        if is_dataclass(markup):
            return asdict(markup)

        if isinstance(markup, ReplyKeyboardMarkup):
            return {
                "type": MarkupType.REPLY,
                "keyboard": [
                    [button.text for button in row] for row in markup.keyboard
                ],
                "resize_keyboard": markup.resize_keyboard,
                "one_time_keyboard": markup.one_time_keyboard,
                "selective": markup.selective,
            }

        if isinstance(markup, InlineKeyboardMarkup):
            return {
                "type": MarkupType.INLINE,
                "inline_keyboard": [
                    [
                        {
                            "text": btn.text,
                            "callback_data": btn.callback_data,
                            **({"url": btn.url} if btn.url else {}),
                        }
                        for btn in row
                    ]
                    for row in markup.inline_keyboard
                ],
            }

        return {}

    @staticmethod
    def deserialize_markup(data: Dict[str, Any]):
        """
        Десериализует разметку из словаря.

        Возвращает:
        - ReplyKeyboardMarkup
        - InlineKeyboardMarkup
        - None если данные невалидны
        """
        if not isinstance(data, dict):
            return None

        try:
            if data.get("type") == MarkupType.REPLY and "keyboard" in data:
                return ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text=btn) for btn in row]
                        for row in data["keyboard"]
                    ],
                    resize_keyboard=data.get("resize_keyboard", True),
                    one_time_keyboard=data.get("one_time_keyboard", False),
                    selective=data.get("selective", False),
                )

            if data.get("type") == MarkupType.INLINE and "inline_keyboard" in data:
                buttons = []
                for row in data["inline_keyboard"]:
                    row_buttons = []
                    for btn in row:
                        if "url" in btn:
                            row_buttons.append(
                                InlineKeyboardButton(text=btn["text"], url=btn["url"])
                            )
                        else:
                            row_buttons.append(
                                InlineKeyboardButton(
                                    text=btn["text"],
                                    callback_data=btn.get(
                                        "callback_data", f"cb_{btn['text']}"
                                    ),
                                )
                            )
                    buttons.append(row_buttons)

                return InlineKeyboardMarkup(inline_keyboard=buttons)
        except Exception as e:
            logger.error(f"Failed to deserialize markup: {e}")

        return None

    @classmethod
    async def get_state_chain(cls, state: FSMContext) -> List[str]:
        """Возвращает цепочку состояний текущего пользователя."""
        data = await state.get_data()
        return data.get("state_chain", [])

    @classmethod
    async def get_help_context(cls, state: FSMContext) -> str:
        """Возвращает справку на основе текущего состояния."""
        current_state = await state.get_state()
        try:
            from app.bot.constants.messages import ContextHelp

            return ContextHelp.get_help_for_state(current_state)
        except Exception as e:
            logger.error(f"[StateManager] Failed to get help context: {e}")
            return "ℹ️ Справка недоступна для текущего состояния."

    @classmethod
    def clear_cache(cls):
        """Очищает кэш состояний и разметки."""
        cls._state_cache.clear()
        cls._markup_cache.clear()
