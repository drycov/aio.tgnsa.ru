import datetime
import hashlib
import json
import math
import os
import platform
import time
import uuid
from pathlib import Path
from typing import Optional, Any, Dict, List

from prettytable import PrettyTable
from puresnmp.types import TimeTicks
from pyasn1.type.univ import OctetString
from pyasn1_modules.rfc1902 import Counter32
from tabulate import tabulate

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
    def get_os_name():
        return "MacOS" if platform.system() == "Darwin" else platform.system()

    @staticmethod
    def format_human_date(date: datetime.datetime, show_time: bool = True) -> str:
        """Форматирование даты в строку в формате 'гггг-мм-дд чч:мм:сс' или 'гггг-мм-дд'."""
        return date.strftime("%Y-%m-%d %H:%M:%S") if show_time else date.strftime("%Y-%m-%d")

    @staticmethod
    def format_human_date_long(date: datetime.datetime, show_time: bool = True) -> str:
        """Форматирование даты в строку с полным названием месяца 'гггг месяц дд, чч:мм:сс'."""
        return date.strftime("%Y %B %d, %H:%M:%S") if show_time else date.strftime("%Y %B %d")

    @staticmethod
    def format_date_2digit(date: datetime.datetime, show_time: bool = True) -> str:
        """Форматирование даты в строку с двухзначными днями и месяцами 'гг-мм-дд чч:мм:сс'."""
        return date.strftime("%y-%m-%d %H:%M:%S") if show_time else date.strftime("%y-%m-%d")

    @staticmethod
    def seconds_to_str(uptime) -> str:
        """
        Преобразует значение TimeTicks или timedelta в строку в формате 'годы месяцы недели дни часы минуты секунды'.
        """
        # Проверка типа uptime и преобразование в секунды
        if isinstance(uptime, TimeTicks):
            total_seconds = int(uptime) / 100  # Преобразование TimeTicks в секунды
        elif isinstance(uptime, datetime.timedelta):
            total_seconds = int(uptime.total_seconds())  # Преобразование timedelta в секунды
        else:
            total_seconds = int(uptime)  # Если uptime уже в секундах

        # Определяем величины времени
        seconds_in_year = 31536000  # 365 дней
        seconds_in_month = 2592000  # 30 дней
        seconds_in_week = 604800  # 7 дней
        seconds_in_day = 86400
        seconds_in_hour = 3600
        seconds_in_minute = 60

        # Вычисляем годы, месяцы, недели, дни, часы, минуты, секунды
        years = int(total_seconds // seconds_in_year)
        total_seconds %= seconds_in_year
        months = int(total_seconds // seconds_in_month)
        total_seconds %= seconds_in_month
        weeks = int(total_seconds // seconds_in_week)
        total_seconds %= seconds_in_week
        days = int(total_seconds // seconds_in_day)
        total_seconds %= seconds_in_day
        hours = int(total_seconds // seconds_in_hour)
        total_seconds %= seconds_in_hour
        minutes = int(total_seconds // seconds_in_minute)
        seconds = int(total_seconds % seconds_in_minute)

        # Формируем строку с результатом, добавляя только непустые значения
        result = []
        if years > 0:
            result.append(f"{years} {'год' if years == 1 else 'лет' if years >= 5 else 'года'}")
        if months > 0:
            result.append(f"{months} {'месяц' if months == 1 else 'месяцев' if months >= 5 else 'месяца'}")
        if weeks > 0:
            result.append(f"{weeks} {'неделя' if weeks == 1 else 'недель' if weeks >= 5 else 'недели'}")
        if days > 0:
            result.append(f"{days} {'день' if days == 1 else 'дней' if days >= 5 else 'дня'}")
        if hours > 0:
            result.append(f"{hours:02} часов")
        if minutes > 0:
            result.append(f"{minutes:02} минут")
        result.append(f"{seconds:02} секунд")  # Секунды всегда отображаются

        return ' '.join(result)

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
                return data.get(key)
        except FileNotFoundError:
            app_logger.error(f"Файл {file_path} не найден.")
            return None
        except json.JSONDecodeError:
            app_logger.error(f"Ошибка декодирования JSON в файле {file_path}")
            return None

    @staticmethod
    def load_oids() -> dict:
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
        action = f"{__name__}.load_device_data"
        from config import Config  # Импорт внутри функции

        """
        Загружает данные обо всех моделях и их конфигурациях из объединенного JSON-файла.
        """
        file_path = Path(Config.DATA_PATH) / 'device_config.json'
        try:
            with file_path.open("r", encoding="utf-8") as file:
                # app_logger.info(f"Загружены данные устройства из файла {file_path}")
                return json.load(file)
        except FileNotFoundError as e:
            HelperFunctions.log_error(action=action, error=e)
            app_logger.error(LogMessages.FILE_NOT_FOUND.value.format(file_path=file_path))
            return {}
        except json.JSONDecodeError as e:
            HelperFunctions.log_error(action=action, error=e)
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

    @staticmethod
    def to_string(value, encoding='utf-8'):
        """
        Преобразует значение типа OctetString, bytes или hex-строку в обычную строку.
        Если значение уже является строкой, возвращает его без изменений.
        """
        if isinstance(value, (Counter32, OctetString)):
            return value.prettyPrint()  # возвращает строковое значение
        # Преобразуем значение из OctetString в строку
        if isinstance(value, OctetString):
            # Получаем строковое представление из OctetString
            value = value.prettyPrint().encode('latin1').decode(encoding)
        # Преобразуем значение из bytes в строку
        elif isinstance(value, bytes):
            value = value.decode(encoding)
        # Проверяем, является ли строка шестнадцатеричной после преобразования
        if isinstance(value, str):
            if HelperFunctions.is_hex_string(value):
                try:
                    # Если строка в hex-формате, преобразуем её в текст
                    if value.startswith("0x"):
                        value = value[2:]
                    value = bytes.fromhex(value).decode(encoding)
                except (ValueError, UnicodeDecodeError) as e:
                    # Оставляем исходное значение и логируем ошибку, если декодировать не удалось
                    print(f"Ошибка при декодировании hex: {e}")
                    pass

        return value  # Возвращаем преобразованное значение или исходное, если оно не требует изменений

    @staticmethod
    def is_hex_string(s: str) -> bool:
        """
        Проверяет, является ли строка шестнадцатеричным значением.
        """
        # Убираем префикс "0x" в начале, если он есть
        if s.startswith("0x"):
            s = s[2:]

        # Проверяем, что строка состоит только из hex-символов и имеет чётную длину
        if len(s) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in s):
            try:
                # Пробуем декодировать строку как hex
                bytes.fromhex(s)
                return True
            except ValueError:
                return False
        return False

    @staticmethod
    def table_formatted_output(results, head=None):
        """
        Форматирует результаты в таблицу с опциональным заголовком.

        Args:
            results (list of lists): Данные для отображения в таблице.
            head (list of str, optional): Заголовки столбцов таблицы. По умолчанию None.

        Returns:
            str: Строковое представление таблицы.
        """
        # Создаем таблицу с помощью `tabulate`
        table_string = tabulate(results, headers=head, tablefmt="plain", stralign="center")
        return table_string

    def generate_vlan_table(vlan_data: List[List[Any]]) -> str:
        """
        Генерация таблицы VLAN с ID, именем и портами.

        :param vlan_data: Список данных VLAN в формате [[VLAN ID, VLAN NAME, PORTS], ...]
        :return: Строка с таблицей
        """
        table = PrettyTable()
        table.field_names = ["VLAN ID", "VLAN NAME", "PORTS"]

        for vlan_id, vlan_name, ports in vlan_data:
            table.add_row([vlan_id, vlan_name, ", ".join(map(str, ports))])

        return table.get_string()

    @staticmethod
    def decode_ports(bit_string: bytes) -> List[int]:
        active_ports = []
        for byte_index, byte in enumerate(bit_string):
            for bit_index in range(8):
                if byte & (1 << bit_index):
                    active_ports.append(byte_index * 8 + bit_index + 1)  # Порты начинаются с 1
        return active_ports

    def log_error(*, action: str, error: Exception, host: Optional[str] = None) -> None:
        """
        Логирование ошибок в едином формате. Используйте именованные параметры для гибкости.
        """
        import json
        import traceback

        # Формируем словарь с ошибкой
        error_data = {
            "date": HelperFunctions.get_current_date(),
            "action": action,
            "error": str(error),
            "trace": traceback.format_exc()
        }

        # Добавляем "host", только если он не None
        if host is not None:
            error_data["host"] = host

        # Преобразуем значения bytes в строки, если есть
        for key, value in error_data.items():
            if isinstance(value, bytes):
                error_data[key] = value.decode('utf-8')

        # Сериализация в JSON с ensure_ascii=False
        error_message = json.dumps(error_data, ensure_ascii=False)
        app_logger.error(error_message)
