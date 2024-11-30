import csv
import json
import sqlite3
from pathlib import Path
from pydoc import Helper

from dotenv import load_dotenv

from bot.utils import HelperFunctions

# Загружаем текущие переменные окружения
load_dotenv()


class ConfigService:
    """
    Класс для управления экспортом переменных окружения в файл .env.
    Сервис для работы с конфигурацией.

    """

    @staticmethod
    def export_to_env(file_path: Path, config_object: object):
        """
        Экспортирует текущие настройки в файл .env.

        :param file_path: Путь к файлу .env
        :param config_object: Объект, содержащий конфигурационные параметры
        """
        env_vars = {attr: getattr(config_object, attr) for attr in dir(config_object) if not attr.startswith("__")}

        # Создаём или перезаписываем .env файл
        with file_path.open("w") as env_file:
            for key, value in env_vars.items():
                # Конвертируем значения в строки
                if value is None:
                    value = ""
                env_file.write(f"{key}={value}\n")
        print(f"Конфигурация успешно экспортирована в {file_path}")

    @staticmethod
    def export_to_json(file_path: Path, config_object: object):
        """
        Экспорт конфигурации в JSON.
        """
        # Преобразуем все атрибуты объекта Config в словарь
        config_dict = {
            attr: (str(getattr(config_object, attr)) if isinstance(getattr(config_object, attr), Path) else getattr(
                config_object, attr))
            for attr in dir(config_object)
            if not attr.startswith("__")
        }

        # Записываем конфигурацию в JSON-файл
        with file_path.open("w") as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
        return file_path

    @staticmethod
    def export_to_csv(file_path: Path, config_object: object):
        """
        Экспорт конфигурации в CSV.
        """
        config_dict = {attr: getattr(config_object, attr) for attr in dir(config_object) if not attr.startswith("__")}
        with file_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Key", "Value"])
            for key, value in config_dict.items():
                writer.writerow([key, value])
        return file_path

    @staticmethod
    def export_to_sql(file_path: Path, config_object: object):
        """
        Экспорт конфигурации в читаемый SQL-дамп.
        """
        # Собираем конфигурацию в словарь
        config_dict = {attr: getattr(config_object, attr) for attr in dir(config_object) if not attr.startswith("__")}

        # Путь для текстового SQL-дампа
        sql_dump_path = file_path.with_suffix(".sql")

        # Открываем текстовый файл для записи SQL-дампа
        with sql_dump_path.open("w", encoding="utf-8") as dump_file:
            # Создание таблицы
            dump_file.write("PRAGMA foreign_keys=OFF;\n")
            dump_file.write("BEGIN TRANSACTION;\n")
            dump_file.write("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT);\n")

            # Вставка значений
            for key, value in config_dict.items():
                # Преобразуем значение в строку
                if value is None:
                    value = "NULL"
                elif isinstance(value, str):
                    value = HelperFunctions.escape_value(value)
                    # value = f"'{value.replace('\'', '\'\'')}'"  # Экранирование одиночных кавычек
                dump_file.write(f"INSERT INTO config (key, value) VALUES ('{key}', {value});\n")

            dump_file.write("COMMIT;\n")

        return sql_dump_path

    @staticmethod
    def update_env_variable(file_path: Path, key: str, value: str):
        """
        Обновляет одну переменную окружения в .env.

        :param file_path: Путь к файлу .env
        :param key: Название переменной
        :param value: Значение переменной
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Файл {file_path} не найден.")

        updated = False
        lines = []

        # Читаем текущие строки файла
        with file_path.open("r") as env_file:
            for line in env_file:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    updated = True
                else:
                    lines.append(line)

        # Если ключ не найден, добавляем его в конец
        if not updated:
            lines.append(f"{key}={value}\n")

        # Записываем обновлённые строки обратно в файл
        with file_path.open("w") as env_file:
            env_file.writelines(lines)
        print(f"Переменная {key} успешно обновлена в {file_path}")
