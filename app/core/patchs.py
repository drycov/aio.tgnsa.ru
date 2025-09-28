from pathlib import Path
from typing import List, Optional, Dict, Union

from .config import BASE_DIR

APP_DIR = BASE_DIR / "app"
STATIC_DIR = BASE_DIR / "static"
LOGS_DIR = BASE_DIR / "logs"
ENV_FILE = BASE_DIR / ".env"
TEMPLATES_DIR = BASE_DIR / APP_DIR / "templates"
MEDIA_DIR = BASE_DIR / "media"
CACHE_DIR = BASE_DIR / ".cache"


class ProjectPaths:
    """
    Централизованное управление путями проекта с расширенными возможностями.

    Этот класс предоставляет единый интерфейс для работы с путями проекта,
    включая создание необходимых директорий, доступ к статическим файлам,
    управление логами и медиа-файлами.

    Основные возможности:
    - Автоматическое создание структуры директорий
    - Валидация путей и проверка существования файлов
    - Генерация путей для различных типов файлов
    - Поддержка временных файлов и кэша

    Attributes:
        base_dir (Path): Корневая директория проекта
        app_dir (Path): Директория основного приложения
        static_dir (Path): Директория статических файлов (CSS, JS, изображения)
        logs_dir (Path): Директория для хранения логов
        templates_dir (Path): Директория шаблонов
        media_dir (Path): Директория для загружаемых медиа-файлов
        cache_dir (Path): Директория для временных и кэшированных файлов
    """

    def __init__(self):
        """
        Инициализация путей проекта.

        Создает экземпляр с предопределенными путями к основным директориям проекта.
        Пути инициализируются на основе констант модуля.
        """
        self.base_dir: Path = BASE_DIR
        self.app_dir: Path = APP_DIR
        self.static_dir: Path = STATIC_DIR
        self.logs_dir: Path = LOGS_DIR
        self.templates_dir: Path = TEMPLATES_DIR
        self.media_dir: Path = MEDIA_DIR
        self.cache_dir: Path = CACHE_DIR
        self.env_file: Path = ENV_FILE

    def ensure_directories(self) -> Dict[str, bool]:
        """
        Создает все необходимые директории проекта с проверкой прав доступа.

        Проверяет и создает следующие директории, если они отсутствуют:
        - static/ - для статических файлов
        - templates/ - для шаблонов
        - logs/ - для файлов логов
        - media/ - для загружаемых файлов
        - .cache/ - для временных файлов

        Returns:
            Dict[str, bool]: Словарь с результатами создания директорий,
                где ключ - имя директории, значение - успешность создания.

        Raises:
            PermissionError: Если недостаточно прав для создания директорий
            OSError: При других ошибках файловой системы

        Example:
            >>> paths = ProjectPaths()
            >>> results = paths.ensure_directories()
            >>> print(results)
            {
                'static': True,
                'templates': True,
                'logs': True,
                'media': True,
                'cache': True
            }
        """
        dirs_to_create = {
            "static": self.static_dir,
            "templates": self.templates_dir,
            "logs": self.logs_dir,
            "media": self.media_dir,
            "cache": self.cache_dir,
        }

        results = {}
        for name, path in dirs_to_create.items():
            try:
                path.mkdir(exist_ok=True, parents=True)
                results[name] = True
            except (PermissionError, OSError) as e:
                results[name] = False
                raise PermissionError(
                    f"Не удалось создать директорию {name}: {str(e)}"
                ) from e
        return results

    def get_log_file(
        self, name: str, file_type: str = "log", create_dir: bool = False
    ) -> Path:
        """
        Генерирует путь к файлу лога с указанным именем и расширением.

        Args:
            name (str): Базовое имя файла без расширения.
            file_type (str, optional): Тип/расширение файла. По умолчанию "log".
                Допустимые значения: "log", "json", "txt", "csv".
            create_dir (bool, optional): Создавать директорию, если не существует.
                По умолчанию False.

        Returns:
            Path: Полный путь к файлу лога.

        Raises:
            ValueError: Если указан неподдерживаемый тип файла.

        Example:
            >>> paths = ProjectPaths()
            >>> log_path = paths.get_log_file("app", "json")
            >>> print(log_path)
            /path/to/project/logs/app.json
        """
        valid_types = ["log", "json", "txt", "csv"]
        if file_type.lower() not in valid_types:
            raise ValueError(
                f"Неподдерживаемый тип файла. Допустимые значения: {valid_types}"
            )

        if create_dir:
            self.logs_dir.mkdir(exist_ok=True, parents=True)

        return self.logs_dir / f"{name}.{file_type.lower()}"

    def get_static_file(self, filename: str) -> Optional[Path]:
        """
        Проверяет существование и возвращает путь к статическому файлу.

        Args:
            filename (str): Имя файла или относительный путь внутри static/.

        Returns:
            Optional[Path]: Полный путь к файлу, если он существует, иначе None.

        Example:
            >>> paths = ProjectPaths()
            >>> css_file = paths.get_static_file("css/styles.css")
            >>> if css_file:
            ...     print(f"Файл найден: {css_file}")
        """
        file_path = self.static_dir / filename
        return file_path if file_path.exists() else None

    def get_media_path(self, subpath: str = "", create_subdir: bool = False) -> Path:
        """
        Генерирует путь к файлу или директории в медиа-хранилище.

        Args:
            subpath (str, optional): Поддиректория или имя файла.
            create_subdir (bool, optional): Создать поддиректорию, если не существует.

        Returns:
            Path: Полный путь к медиа-файлу или директории.

        Example:
            >>> paths = ProjectPaths()
            >>> img_path = paths.get_media_path("uploads/images/profile.jpg")
        """
        full_path = self.media_dir / subpath
        if create_subdir:
            full_path.parent.mkdir(exist_ok=True, parents=True)
        return full_path

    def get_cache_file(
        self, key: str, extension: str = "tmp", create_dir: bool = True
    ) -> Path:
        """
        Генерирует путь к временному или кэшированному файлу.

        Args:
            key (str): Уникальный ключ/имя для файла.
            extension (str, optional): Расширение файла. По умолчанию "tmp".
            create_dir (bool, optional): Создать директорию кэша при необходимости.

        Returns:
            Path: Полный путь к файлу в директории кэша.

        Example:
            >>> paths = ProjectPaths()
            >>> cache_file = paths.get_cache_file("user_data", "json")
        """
        if create_dir:
            self.cache_dir.mkdir(exist_ok=True, parents=True)
        return self.cache_dir / f"{key}.{extension}"

    def find_files(self, pattern: str, recursive: bool = True) -> List[Path]:
        """
        Поиск файлов по шаблону в проекте.

        Args:
            pattern (str): Шаблон для поиска (например, "*.py").
            recursive (bool, optional): Рекурсивный поиск. По умолчанию True.

        Returns:
            List[Path]: Список найденных файлов.

        Example:
            >>> paths = ProjectPaths()
            >>> py_files = paths.find_files("*.py")
        """
        if recursive:
            return list(self.base_dir.rglob(pattern))
        return list(self.base_dir.glob(pattern))

    def relative_to_base(self, path: Union[str, Path]) -> Path:
        """
        Преобразует абсолютный путь в относительный относительно base_dir.

        Args:
            path (Union[str, Path]): Абсолютный путь для преобразования.

        Returns:
            Path: Относительный путь.

        Raises:
            ValueError: Если путь не находится внутри base_dir.

        Example:
            >>> paths = ProjectPaths()
            >>> rel_path = paths.relative_to_base("/path/to/project/app/views.py")
            >>> print(rel_path)
            app/views.py
        """
        abs_path = Path(path).resolve()
        try:
            return abs_path.relative_to(self.base_dir.resolve())
        except ValueError as e:
            raise ValueError(
                f"Путь {abs_path} не находится внутри проекта ({self.base_dir})"
            ) from e


# Глобальный экземпляр для использования во всем проекте
project_paths = ProjectPaths()
