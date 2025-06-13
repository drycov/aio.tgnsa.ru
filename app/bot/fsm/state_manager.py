from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, Message
)
from typing import Optional, Dict, Any




class StateManager:
    """
    FSM-менеджер с поддержкой StateGroup, истории состояний и сериализации разметки.
    """

    @staticmethod
    async def set_state_with_previous(
        state: FSMContext,
        new_state: State,
        display_data: Optional[Dict[str, Any]] = None,
        action: Optional[str] = None
    ) -> None:
        current_state = await state.get_state()
        new_state_str = new_state.state

        if current_state != new_state_str:
            session_data = await state.get_data()
            display_history = session_data.get("display_history", {})
            action_history = session_data.get("action_history", {})

            if display_data and "reply_markup" in display_data:
                display_data["reply_markup"] = StateManager.serialize_markup(display_data["reply_markup"])

            if current_state:
                display_history[new_state_str] = display_data or {}
                action_history[new_state_str] = action or None

            await state.update_data(
                previous_state=current_state,
                display_history=display_history,
                action_history=action_history
            )

        await state.set_state(new_state)

    @staticmethod
    async def handle_back_action(state: FSMContext, message: Message) -> None:
        data = await state.get_data()
        previous_state = data.get("previous_state")
        display_history = data.get("display_history", {})
        action_history = data.get("action_history", {})

        is_online = data.get("is_online", False)
        is_admin = data.get("is_admin", False)

        if previous_state and action_history.get(previous_state) not in ["input_field", "input", None]:
            await StateManager._handle_previous_state(previous_state, display_history, state, message)
        else:
            await StateManager._handle_no_previous_state(is_online, is_admin, state, message)

    @staticmethod
    async def _handle_previous_state(
        previous_state: str,
        display_history: Dict[str, Any],
        state: FSMContext,
        message: Message
    ) -> None:
        display_data = display_history.get(previous_state, {"text": "🔙 Возврат на предыдущий шаг"})

        if "reply_markup" in display_data and isinstance(display_data["reply_markup"], dict):
            display_data["reply_markup"] = StateManager.deserialize_markup(display_data["reply_markup"])

        await state.set_state(previous_state)
        await message.answer(**display_data)

    # @staticmethod
    # async def _handle_no_previous_state(
    #     is_online: bool,
    #     is_admin: bool,
    #     state: FSMContext,
    #     message: Message
    # ) -> None:
    #     """
    #     Отправка пользователя в корневое меню.
    #     """
    #     await state.set_state(MainCommands.MAIN_MENU)
    #     keyboard = generate_main_keyboard(is_admin)
    #     await message.answer(text=MenuLabels.MAIN_MENU.value, reply_markup=keyboard)

    @staticmethod
    def serialize_markup(markup) -> Dict[str, Any]:
        if isinstance(markup, ReplyKeyboardMarkup):
            return {
                "type": "reply",
                "keyboard": [[button.text for button in row] for row in markup.keyboard]
            }
        elif isinstance(markup, InlineKeyboardMarkup):
            return {
                "type": "inline",
                "inline_keyboard": [[button.text for button in row] for row in markup.inline_keyboard]
            }
        return {}

    @staticmethod
    def deserialize_markup(data: Dict[str, Any]):
        if not isinstance(data, dict):
            return None

        if data.get("type") == "reply" and "keyboard" in data:
            keyboard = [[KeyboardButton(text=btn) for btn in row] for row in data["keyboard"]]
            return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

        elif data.get("type") == "inline" and "inline_keyboard" in data:
            inline = [
                [InlineKeyboardButton(text=btn, callback_data=f"cb_{btn}") for btn in row]
                for row in data["inline_keyboard"]
            ]
            return InlineKeyboardMarkup(inline_keyboard=inline)

        return None
