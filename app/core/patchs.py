import os
from pathlib import Path
from typing import List, Optional

from .config import BASE_DIR

APP_DIR = BASE_DIR / "app"
STATIC_DIR = BASE_DIR / "static"
LOGS_DIR = BASE_DIR / "logs"
ENV_FILE = BASE_DIR / ".env"
TEMPLATES_DIR = BASE_DIR / APP_DIR / "templates"


class ProjectPaths:
    """
    Управление путями проекта FastBill.

    Этот класс предоставляет централизованное управление путями проекта,
    включая работу с логами, статическими файлами и структурой директорий.

    Attributes:
        base_dir (Path): Корневая директория проекта
        app_dir (Path): Директория приложения
        static_dir (Path): Директория для статических файлов
        logs_dir (Path): Директория для логов

    Example:
        >>> paths = ProjectPaths()
        >>> paths.ensure_directories()
        >>> log_path = paths.get_log_file("app")
        >>> static_file = paths.get_static_file("style.css")
    """

    def __init__(self):
        """Инициализация путей проекта."""
        self.base_dir: Path = BASE_DIR
        self.app_dir: Path = APP_DIR
        self.static_dir: Path = STATIC_DIR
        self.logs_dir: Path = LOGS_DIR
        self.templates_dir: Path = TEMPLATES_DIR

    def ensure_directories(self) -> None:
        """
        Создает необходимые директории проекта.

        Проверяет и создает основные директории проекта, если они отсутствуют:
        - static/
        - templates/
        - logs/

        Raises:
            PermissionError: Если нет прав на создание директорий
        """
        directories = [
            self.static_dir,
            self.templates_dir,
            self.logs_dir
        ]
        for directory in directories:
            directory.mkdir(exist_ok=True, parents=True)

    def get_log_file(self, name: str, file_type: str = "json") -> Path:
        """
        Возвращает путь к файлу лога.

        Args:
            name (str): Имя лог файла без расширения
            file_type (str, optional): Тип файла. Defaults to "json".
                Допустимые значения: "json", "log", "txt"

        Returns:
            Path: Объект Path, представляющий путь к файлу лога

        Example:
            >>> paths = ProjectPaths()
            >>> log_path = paths.get_log_file("app", "json")
            >>> print(log_path)
            /path/to/project/logs/app.json
        """
        if file_type.lower() not in ["json", "log", "txt"]:
            file_type = "json"
        return self.logs_dir / f"{name}.{file_type}"

    def get_static_file(self, filename: str) -> Optional[Path]:
        """
        Возвращает путь к статическому файлу.

        Args:
            filename (str): Имя файла в директории static

        Returns:
            Optional[Path]: Путь к файлу если он существует, иначе None

        Example:
            >>> paths = ProjectPaths()
            >>> css_file = paths.get_static_file("style.css")
            >>> if css_file:
            ...     print("Файл существует")
        """
        file_path = self.static_dir / filename
        return file_path if file_path.exists() else None


# Создаем экземпляр для использования в приложении
project_paths = ProjectPaths()
