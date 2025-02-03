from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Message

from bot.constants import MenuLabels
from bot.constants.states import MainCommands
from bot.keyboards import generate_main_keyboard


class StateManager:
    """
    Класс для управления состояниями FSM в aiogram.
    Позволяет устанавливать состояния с сохранением предыдущего,
    сериализовать и десериализовать разметку, а также обрабатывать возврат на предыдущий шаг.
    """

    @staticmethod
    async def set_state_with_previous(state: FSMContext, new_state: State, display_data: dict = None,
                                      action: str = None):
        """
        Устанавливает новое состояние, сохраняя текущее как предыдущее.

        :param state: Объект FSMContext.
        :param new_state: Новое состояние.
        :param display_data: Данные для отображения (необязательно).
        :param action: Специфическое действие для истории (необязательно).
        """
        current_state = await state.get_state()
        if current_state != str(new_state):
            session_data = await state.get_data()
            display_history = session_data.get("display_history", {})
            action_history = session_data.get("action_history", {})

            if display_data and "reply_markup" in display_data:
                display_data["reply_markup"] = StateManager.serialize_markup(display_data["reply_markup"])

            if current_state:
                display_history[str(new_state.state)] = display_data or {}
                action_history[str(new_state.state)] = action or None

            await state.update_data(previous_state=str(current_state), display_history=display_history,
                                    action_history=action_history)
        await state.set_state(new_state)

    @staticmethod
    def serialize_markup(markup) -> dict:
        """
        Преобразует разметку в словарь для сохранения.

        :param markup: Объект ReplyKeyboardMarkup или InlineKeyboardMarkup.
        :return: Сериализованный словарь разметки.
        """
        if isinstance(markup, ReplyKeyboardMarkup):
            return {"keyboard": [[button.text for button in row] for row in markup.keyboard]}
        elif isinstance(markup, InlineKeyboardMarkup):
            return {"inline_keyboard": [[button.text for button in row] for row in markup.inline_keyboard]}
        return {}

    @staticmethod
    def deserialize_markup(data: dict):
        """
        Восстанавливает объект разметки из словаря.

        :param data: Сериализованный словарь разметки.
        :return: Объект ReplyKeyboardMarkup или InlineKeyboardMarkup, либо None.
        """
        if "keyboard" in data:
            keyboard = [[KeyboardButton(text=button_text) for button_text in row] for row in data["keyboard"]]
            return ReplyKeyboardMarkup(keyboard=keyboard)
        elif "inline_keyboard" in data:
            inline_keyboard = [
                [InlineKeyboardButton(text=button_text, callback_data=f"callback_{button_text}") for button_text in row]
                for row in data["inline_keyboard"]
            ]
            return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
        return None

    @staticmethod
    async def handle_back_action(state: FSMContext, message: Message):
        """
        Обрабатывает действие «Назад», возвращая пользователя к предыдущему состоянию.

        :param state: Объект FSMContext.
        :param message: Сообщение пользователя.
        """
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
    async def _handle_previous_state(previous_state: str, display_history: dict,
                                     state: FSMContext, message: Message):
        """
        Восстанавливает предыдущее состояние и отправляет сообщение.

        :param previous_state: Предыдущее состояние.
        :param display_history: История отображения.
        :param state: Объект FSMContext.
        :param message: Сообщение пользователя.
        """
        display_data = display_history.get(previous_state, {"text": "Возврат на предыдущий шаг"})
        if "reply_markup" in display_data and isinstance(display_data["reply_markup"], dict):
            display_data["reply_markup"] = StateManager.deserialize_markup(display_data["reply_markup"])
        await state.set_state(previous_state)
        await message.answer(**display_data)

    @staticmethod
    async def _handle_no_previous_state(is_online: bool, is_admin: bool, state: FSMContext, message: Message):
        """
        Обрабатывает ситуацию, когда нет предыдущего состояния.

        :param is_online: Флаг активности пользователя.
        :param is_admin: Флаг администратора.
        :param state: Объект FSMContext.
        :param message: Сообщение пользователя.
        """
        await state.set_state(MainCommands.MAIN_MENU)
        keyboard = generate_main_keyboard(is_admin)
        await message.answer(text=MenuLabels.MAIN_MENU.value, reply_markup=keyboard)
