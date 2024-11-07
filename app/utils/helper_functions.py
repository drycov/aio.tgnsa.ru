import datetime
import hashlib
import json
import math
import os
import time
from pathlib import Path
from sys import platform
from typing import Optional, Any, Dict

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message

from app.constants import NetworkMessages, LogMessages
from app.utils.logger_instance import app_logger


class HelperFunctions:

    @staticmethod
    def delay_ms(ms: int):
        """Задержка выполнения на указанное количество миллисекунд."""
        time.sleep(ms / 1000)

    @staticmethod
    def get_current_date() -> str:
        """Получение текущей даты и времени в формате 'дд-мм-гггг чч:мм:сс'."""
        return datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    @staticmethod
    def get_text_dimensions(text: str, font: str) -> tuple:
        """Определение приблизительных размеров текста (ширина и высота)."""
        # Имитация измерения текста — длина строки * 10 для ширины
        return len(text) * 10, 20

    @staticmethod
    def noop():
        """Пустая функция-заглушка, которая ничего не делает."""
        pass

    @staticmethod
    def get_app_token() -> str:
        """Получение токена для приложения на основе переменной окружения APP_TYPE."""
        return os.getenv("DEV_TOKEN") if os.getenv("APP_TYPE") == "DEV" else os.getenv("PROD_TOKEN")

    @staticmethod
    def get_os_type() -> str:
        """Определение типа операционной системы."""
        return "MacOS" if platform.system() == "Darwin" else platform.system()

    @staticmethod
    def format_human_date(date: datetime.datetime) -> str:
        """Форматирование даты в строку в формате 'гггг-мм-дд чч:мм:сс'."""
        return date.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def format_human_date_long(date: datetime.datetime) -> str:
        """Форматирование даты в строку с полным названием месяца 'гггг месяц дд, чч:мм:сс'."""
        return date.strftime("%Y %B %d, %H:%M:%S")

    @staticmethod
    def format_date_2digit(date: datetime.datetime) -> str:
        """Форматирование даты в строку с двухзначными днями и месяцами 'гг-мм-дд чч:мм:сс'."""
        return date.strftime("%y-%m-%d %H:%M:%S")

    @staticmethod
    def seconds_to_str(uptime: int) -> str:
        """Преобразование секунд в строку в формате 'дни часы минуты секунды'."""
        return f"{int(uptime / 86400):02} дней {int((uptime % 86400) / 3600):02} часов " \
               f"{int((uptime % 3600) / 60):02} минут {int(uptime % 60):02} секунд"

    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """Генерация верификационного кода заданной длины (по умолчанию 6 цифр)."""
        return ''.join([str(int(time.time()) % 10) for _ in range(length)])

    @staticmethod
    def generate_email_template(mail_data: str, template: str) -> str:
        """Генерация HTML-шаблона с указанными данными и названием шаблона."""
        return f"<html><body><h3>{template}</h3>{mail_data}</body></html>"

    @staticmethod
    def generate_verification_codes() -> dict:
        """Генерация двух уникальных верификационных кодов с помощью MD5 хеширования."""
        return {
            "code_A": hashlib.md5(os.urandom(24)).hexdigest(),
            "code_B": hashlib.md5(os.urandom(24)).hexdigest()
        }

    @staticmethod
    def parse_telegram_command(text: str) -> dict:
        """Парсинг команды Telegram, возвращает словарь параметров."""
        return {str(i - 1): word for i, word in enumerate(text.strip().split())}

    @staticmethod
    def convert_mW_to_dBW(val: float) -> float:
        """Преобразование мощности в милливаттах (мВт) в децибелы (дБм)."""
        return round(10 * (math.log10(val) - 3), 2)

    @staticmethod
    def convert_hex_to_binary(input_string: str) -> str:
        """Преобразование шестнадцатеричной строки в двоичное представление."""
        return ''.join(bin(int(char, 16))[2:].zfill(4) for char in input_string)

    @staticmethod
    def hash_user_id(user_id: str) -> str:
        """Хеширование идентификатора пользователя с помощью SHA-256."""
        return hashlib.sha256(user_id.encode()).hexdigest()

    @staticmethod
    def interface_loader(key: str, filename: str) -> Optional[Any]:
        """
        Загрузка интерфейса из JSON-файла.
        """
        file_path = os.path.join(os.path.dirname(__file__), filename)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get(key)
        except Exception as error:
            print(NetworkMessages.ERROR_FILE_READ.value.format(file_path=file_path, error=error))
            return None

    @staticmethod
    def load_interface_data(key: str, filename: str) -> Any:
        from config import Config  # Импорт внутри функции

        """
        Загружает конфигурацию интерфейсов из JSON-файла.
        """
        file_path = Path(Config.DATA_PATH) / f"{filename}.json"
        try:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                # app_logger.info(f"Загружены данные из файла {file_path}")
                return data.get(key)
        except FileNotFoundError:
            app_logger.error(f"Файл {file_path} не найден.")
            return None
        except json.JSONDecodeError:
            app_logger.error(f"Ошибка декодирования JSON в файле {file_path}")
            return None

    @staticmethod
    def load_oids(file_path: str) -> dict:
        from config import Config  # Импорт внутри функции

        """
        Загружает OID'ы из JSON-файла.
        """
        file_path = Path(Config.DATA_PATH) / "oid.json"
        try:
            with file_path.open("r", encoding="utf-8") as file:
                # app_logger.info(f"Загружены данные устройства из файла {file_path}")
                return json.load(file)
        except FileNotFoundError:
            app_logger.error(LogMessages.FILE_NOT_FOUND.value.format(file_path=file_path))
            return {}
        except json.JSONDecodeError:
            app_logger.error(LogMessages.JSON_DECODE_ERROR.value.format(file_path=file_path))
            return {}

    @staticmethod
    def load_device_data() -> Dict[str, Dict[str, Any]]:
        from config import Config  # Импорт внутри функции

        """
        Загружает данные обо всех моделях и их конфигурациях из объединенного JSON-файла.
        """
        file_path = Path(Config.DATA_PATH) / 'device_config.json'
        try:
            with file_path.open("r", encoding="utf-8") as file:
                # app_logger.info(f"Загружены данные устройства из файла {file_path}")
                return json.load(file)
        except FileNotFoundError:
            app_logger.error(LogMessages.FILE_NOT_FOUND.value.format(file_path=file_path))
            return {}
        except json.JSONDecodeError:
            app_logger.error(LogMessages.JSON_DECODE_ERROR.value.format(file_path=file_path))
            return {}

    @staticmethod
    def validate(text: str, replace: str, labels: dict) -> str:
        """
        Проверка валидности текста и замена, если содержатся команды или метки.
        """
        is_command = text.strip().startswith("/")
        contains_label_or_command = any(label in text for label in labels.values())

        return replace if is_command or contains_label_or_command else text

    @staticmethod
    def get_oid(oids: dict, group: str, name: str, subcategory: str = None) -> str:
        """
        Функция для получения OID по имени и группе.
        Параметры:
            oids (dict): Словарь OID'ов, загруженный из JSON.
            group (str): Основная группа OID'ов.
            name (str): Название OID в группе.
            subcategory (str, optional): Подкатегория OID, если требуется.
        Возвращает:
            str: OID или сообщение об ошибке.
        """
        try:
            if subcategory:
                return oids[group][subcategory][name]
            return oids[group][name]
        except KeyError:
            return f"OID '{name}' не найден в группе '{group}'"


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
