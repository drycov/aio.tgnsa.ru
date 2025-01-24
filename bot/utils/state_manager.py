from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Message

from bot.constants import MenuLabels
from bot.constants.states import MainCommands
from bot.keyboards import on_enter_keyboard, generate_main_keyboard


class StateManager:
    @staticmethod
    async def set_state_with_previous(state: FSMContext, new_state: State, display_data: dict = None,
                                      action: str = None):
        """
        Устанавливает новое состояние, сохраняя текущее состояние как предыдущее
        и добавляя данные для отображения и записи action history, если состояние изменилось.

        Args:
            state (FSMContext): Объект контекста FSM.
            new_state (State): Новое состояние для установки.
            display_data (dict, optional): Данные для отображения, которые нужно сохранить.
            action (str, optional): Специфическое действие, которое нужно сохранить в истории действий.
        """
        # Получаем текущее состояние
        current_state = await state.get_state()

        # Если состояние изменилось, сохраняем текущее как предыдущее и добавляем данные для отображения
        if current_state != str(new_state):  # Преобразуем `new_state` в строку для сравнения
            session_data = await state.get_data()
            display_history = session_data.get("display_history", {})
            action_history = session_data.get("action_history", {})

            # Сериализуем разметку, если она присутствует в `display_data`
            if display_data and "reply_markup" in display_data:
                display_data["reply_markup"] = StateManager.serialize_markup(display_data["reply_markup"])

            # Сохраняем `display_data` и `action` для нового состояния
            if current_state:
                display_history[str(new_state.state)] = display_data or {}
                action_history[str(new_state.state)] = action or None

            # Обновляем данные сессии с предыдущим состоянием и историей отображения
            await state.update_data(previous_state=str(current_state), display_history=display_history,
                                    action_history=action_history)

        # Устанавливаем новое состояние
        await state.set_state(new_state)

    @staticmethod
    def serialize_markup(markup) -> dict:
        """
        Преобразует объект `ReplyKeyboardMarkup` или `InlineKeyboardMarkup` в словарь для сохранения.
        """
        if isinstance(markup, ReplyKeyboardMarkup):
            # Сериализация для ReplyKeyboardMarkup
            return {
                "keyboard": [[button.text for button in row] for row in markup.keyboard],
                "resize_keyboard": markup.resize_keyboard,
                "one_time_keyboard": markup.one_time_keyboard,
                "selective": markup.selective,
                "is_persistent": markup.is_persistent,
                "input_field_placeholder": markup.input_field_placeholder,
            }
        elif isinstance(markup, InlineKeyboardMarkup):
            # Сериализация для InlineKeyboardMarkup
            return {
                "inline_keyboard": [[button.text for button in row] for row in markup.inline_keyboard],
            }
        else:
            # Возвращаем None или пустой словарь, если тип markup не поддерживается
            return {}

    @staticmethod
    def deserialize_markup(data: dict):
        """
        Преобразует словарь обратно в объект `ReplyKeyboardMarkup` или `InlineKeyboardMarkup`.
        """
        if "keyboard" in data:
            # Восстанавливаем объект `ReplyKeyboardMarkup`
            keyboard = [[KeyboardButton(text=button_text) for button_text in row] for row in data["keyboard"]]
            return ReplyKeyboardMarkup(
                keyboard=keyboard,
                parse_mode=data.get("parse_mode"),
                one_time_keyboard_reply=data.get("one_time_keyboard_reply"),
                selective=data.get("selective"),
                is_persistent=data.get("is_persistent"),
                input_field_placeholder=data.get("input_field_placeholder"),

            )
        elif "inline_keyboard" in data:
            # Восстанавливаем объект `InlineKeyboardMarkup`
            inline_keyboard = [
                [
                    InlineKeyboardButton(text=button_text, callback_data=f"callback_{button_text}")
                    for button_text in row
                ]
                for row in data["inline_keyboard"]
            ]
            return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
        else:
            # Если формат данных не распознан, возвращаем None или обрабатываем это иначе
            return None

    @staticmethod
    async def handle_back_action(state: FSMContext, message: Message):
        """
        Обрабатывает действие «Назад», возвращая пользователя к предыдущему состоянию или в начальное состояние с разметкой,
        при этом избегая возврата к состояниям ввода.
        """
        # Получаем данные о предыдущем состоянии и истории отображения
        data = await state.get_data()
        previous_state = data.get("previous_state")
        display_history = data.get("display_history", {})
        action_history = data.get("action_history", {})
        is_online = data.get("is_online", False)
        is_admin = data.get("is_admin", False)

        # Проверка на предыдущее состояние
        if previous_state and action_history.get(previous_state) not in ["input_field", "input", None]:
            await StateManager._handle_previous_state(previous_state, display_history, action_history, state, message)
        else:
            await StateManager._handle_no_previous_state(is_online, is_admin, state, message)

    @staticmethod
    async def _handle_previous_state(previous_state: str, display_history: dict, action_history: dict,
                                     state: FSMContext, message: Message):
        """
        Восстанавливает предыдущее состояние и отображение, если оно существует.
        """
        display_data = display_history.get(previous_state, {})
        # action_data = action_history.get(previous_state, None)

        display_data["text"] = display_data.get("text", "Возврат на предыдущий шаг")

        # Восстанавливаем разметку, если она была сериализована
        if "reply_markup" in display_data and isinstance(display_data["reply_markup"], dict):
            display_data["reply_markup"] = StateManager.deserialize_markup(display_data["reply_markup"])

        # Устанавливаем предыдущее состояние и отправляем сообщение с восстановленными данными
        await state.set_state(previous_state)
        await message.answer(**display_data)

    @staticmethod
    async def _handle_no_previous_state(is_online: bool, is_admin: bool, state: FSMContext, message: Message):
        """
        Обрабатывает ситуацию, когда нет предыдущего состояния или оно связано с полем ввода.
        """
        if is_online:
            # Если пользователь находится в сети, возвращаемся к начальному состоянию
            await state.set_state(MainCommands.MAIN_MENU)
            keyboard = generate_main_keyboard(is_admin)
            await message.answer(
                text=MenuLabels.MAIN_MENU.value,
                reply_markup=keyboard  # Устанавливаем разметку главного меню
            )
        else:
            # Если предыдущего состояния нет или оно связано с полем ввода, возвращаемся к начальному состоянию
            await state.set_state(MainCommands.MAIN_MENU)
            keyboard = generate_main_keyboard(is_admin)
        await message.answer(
                text=MenuLabels.MAIN_MENU.value,
                reply_markup=keyboard  # Устанавливаем разметку главного меню
            )
