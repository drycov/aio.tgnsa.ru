import importlib
import inspect
from typing import Type, Union, List, Generator, Optional, Set
from pathlib import Path
from aiogram.fsm.state import State, StatesGroup
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Конфигурация
DEFAULT_PROJECT_ROOTS = ["app", "plugins"]
EXCLUDED_DIRS = {"__pycache__", "__init__.py", "tests"}
CACHE_SIZE = 100  # Размер кэша для результатов поиска


def discover_py_modules(
    base_dirs: List[Union[str, Path]],
) -> Generator[str, None, None]:
    """
    Находит все Python модули в указанных директориях.

    Args:
        base_dirs: Список базовых директорий для поиска

    Yields:
        Имена модулей в точечной нотации (например 'app.bot.states.main')
    """
    for base_dir in base_dirs:
        base_path = Path(base_dir)
        if not base_path.exists():
            logger.debug(f"Директория не существует: {base_path}")
            continue

        for file in base_path.rglob("*.py"):
            # Пропускаем служебные директории и файлы
            if any(excluded in file.parts for excluded in EXCLUDED_DIRS):
                continue

            # Преобразуем путь в модуль
            try:
                rel_path = file.relative_to(Path.cwd())
            except ValueError:
                # Если файл вне текущего рабочего каталога
                rel_path = file

            module_path = ".".join(rel_path.with_suffix("").parts)
            yield module_path


@lru_cache(maxsize=CACHE_SIZE)
def get_state_groups_from_module(module_name: str) -> List[Type[StatesGroup]]:
    """
    Извлекает все классы StatesGroup из указанного модуля.

    Args:
        module_name: Имя модуля для анализа

    Returns:
        Список найденных классов StatesGroup
    """
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        logger.debug(f"Не удалось импортировать модуль {module_name}: {e}")
        return []

    groups = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, StatesGroup) and obj is not StatesGroup:
            groups.append(obj)

    return groups


def find_all_state_groups(
    project_roots: List[Union[str, Path]] = DEFAULT_PROJECT_ROOTS,
) -> List[Type[StatesGroup]]:
    """
    Находит все классы StatesGroup в проекте.

    Args:
        project_roots: Список корневых директорий для поиска

    Returns:
        Список всех найденных классов StatesGroup
    """
    found_groups = []
    processed_modules = set()

    for module_name in discover_py_modules(project_roots):
        if module_name in processed_modules:
            continue

        groups = get_state_groups_from_module(module_name)
        if groups:
            found_groups.extend(groups)
            processed_modules.add(module_name)
            logger.debug(f"Найдены StatesGroups в {module_name}: {groups}")

    return found_groups


def restore_state_from_string(state_str: Optional[str]) -> Union[State, str, None]:
    """
    Восстанавливает объект State из строки, ища во всех StatesGroup проекта.

    Args:
        state_str: Строка с именем состояния или None

    Returns:
        Объект State, исходную строку или None если входной аргумент был None
    """
    if state_str is None:
        return None

    # Кэшируем найденные группы для производительности
    state_groups = find_all_state_groups()

    for group in state_groups:
        for attr_name in dir(group):
            attr = getattr(group, attr_name)
            if isinstance(attr, State) and attr.state == state_str:
                logger.debug(f"Найдено соответствие состояния: {state_str} -> {attr}")
                return attr

    return state_str


def get_all_states() -> Set[str]:
    """
    Возвращает все возможные состояния из всех StatesGroup проекта.

    Returns:
        Множество строковых представлений состояний
    """
    states = set()
    for group in find_all_state_groups():
        for attr_name in dir(group):
            attr = getattr(group, attr_name)
            if isinstance(attr, State):
                states.add(attr.state)
    return states


def validate_state(state_str: str) -> bool:
    """
    Проверяет, существует ли указанное состояние в проекте.

    Args:
        state_str: Строка с именем состояния для проверки

    Returns:
        True если состояние существует, False в противном случае
    """
    return state_str in get_all_states()
