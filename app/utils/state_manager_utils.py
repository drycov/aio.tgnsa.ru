from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message


class StateManager:
    @staticmethod
    async def set_state_with_previous(state: FSMContext, new_state: State, display_data: dict = None):
        """
        Устанавливает новое состояние, сохраняя текущее состояние как предыдущее
        и добавляя данные для отображения, если состояние изменилось.

        Args:
            state (FSMContext): Объект контекста FSM.
            new_state (State): Новое состояние для установки.
            display_data (dict, optional): Данные для отображения, которые нужно сохранить.
        """
        # Получаем текущее состояние
        current_state = await state.get_state()

        # Если состояние изменилось, сохраняем текущее как предыдущее и добавляем данные для отображения
        if current_state != str(new_state):  # Преобразуем `new_state` в строку для сравнения

            session_data = await state.get_data()
            display_history = session_data.get("display_history", {})

            # Сериализуем разметку, если она присутствует в `display_data`
            if display_data and "reply_markup" in display_data:
                display_data["reply_markup"] = StateManager.serialize_markup(display_data["reply_markup"])

            # Сохраняем `display_data` для нового состояния в строковом формате
            if current_state:
                display_history[str(new_state.state)] = display_data or {}

            # Обновляем данные сессии с предыдущим состоянием и историей отображения
            await state.update_data(previous_state=str(current_state), display_history=display_history)

        # Устанавливаем новое состояние
        await state.set_state(new_state)

    @staticmethod
    def serialize_markup(markup: ReplyKeyboardMarkup) -> dict:
        """Преобразует объект `ReplyKeyboardMarkup` в словарь для сохранения."""
        return {
            "keyboard": [[button.text for button in row] for row in markup.keyboard],
            "resize_keyboard": markup.resize_keyboard,
            "one_time_keyboard": markup.one_time_keyboard,
        }

    @staticmethod
    def deserialize_markup(data: dict) -> ReplyKeyboardMarkup:
        """Преобразует словарь обратно в объект `ReplyKeyboardMarkup`."""
        keyboard = [[KeyboardButton(text=button_text) for button_text in row] for row in data["keyboard"]]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=data["resize_keyboard"],
                                   one_time_keyboard=data["one_time_keyboard"])

    @staticmethod
    async def handle_back_action(state: FSMContext, message: Message):
        """
        Обрабатывает действие «Назад», возвращая пользователя к предыдущему состоянию и отображая данные.

        Args:
            state (FSMContext): Контекст FSM для пользователя.
            message (Message): Сообщение, на которое ответит бот.
        """
        # Получаем данные о предыдущем состоянии и историю отображения
        data = await state.get_data()
        previous_state = data.get("previous_state")
        display_history = data.get("display_history", {})

        # Проверяем, есть ли данные для отображения предыдущего состояния
        if previous_state:
            display_data = display_history.get(previous_state, {})
            # Устанавливаем текст по умолчанию, если его нет в display_data
            display_data["text"] = display_data.get("text", "Возврат на предыдущий шаг")
            # Восстанавливаем разметку, если она была сериализована
            if "reply_markup" in display_data and isinstance(display_data["reply_markup"], dict):
                display_data["reply_markup"] = StateManager.deserialize_markup(display_data["reply_markup"])

            # Устанавливаем предыдущее состояние
            await state.set_state(previous_state)

            # Отправляем сообщение с восстановленным текстом и клавиатурой
            await message.answer(**display_data)
        else:
            # Если нет предыдущего состояния, уведомляем пользователя
            await message.answer("Нет предыдущего состояния для возврата.")
