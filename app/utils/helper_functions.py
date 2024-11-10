import datetime
import hashlib
import json
import math
import os
import time
import uuid
from pathlib import Path
from sys import platform
from typing import Optional, Any, Dict

from app.constants import NetworkMessages, LogMessages
from app.models import Task
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

    @staticmethod
    def generate_task_id(task: Task) -> str:
        """
        Генерация уникального идентификатора задачи на основе даты, исполнителя и случайного суффикса.
        """
        assignee_part = task.assigned_to  # Идентификатор назначенного сотрудника
        unique_suffix = uuid.uuid4().hex[:6]  # Случайный суффикс из 6 символов

        return f"{assignee_part}{unique_suffix}"
