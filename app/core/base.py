import logging
import pkgutil
import importlib
import sys
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

_discovered = False


class Base(DeclarativeBase):
    """Базовый класс для декларативных ORM-моделей SQLAlchemy 2.x."""
    pass


def autodiscover_models(packages: list[str] | None = None) -> list[type[Base]]:
    """
    Импортирует все найденные SQLAlchemy-модели (включая плагины).
    Ищет как app.models.*, так и app.plugins.*.models.*
    """
    global _discovered
    if _discovered:
        return _get_registered_models()

    base_packages = packages or ["app.models", "app.plugins"]

    for base in base_packages:
        try:
            spec = importlib.util.find_spec(base)
            if not spec or not spec.submodule_search_locations:
                logger.debug(f"[autodiscover_models] Пропускаем {base} — нет пакета")
                continue

            package_path = list(spec.submodule_search_locations)[0]

            for _, module_name, is_pkg in pkgutil.walk_packages([package_path], base + "."):
                # ⚡ теперь импортируем и models.py, и подпакеты models.*
                if not (module_name.endswith("models") or ".models" in module_name):
                    continue

                if module_name in sys.modules:
                    continue

                try:
                    importlib.import_module(module_name)
                    logger.debug(f"[autodiscover_models] Импортирован {module_name}")
                except Exception as e:
                    logger.warning(
                        f"[autodiscover_models] ⚠ Ошибка импорта {module_name}: {e}",
                        exc_info=True,
                    )

        except ModuleNotFoundError:
            logger.debug(f"[autodiscover_models] Пропускаем {base} — модуль не найден")

    _discovered = True
    return _get_registered_models()


def _get_registered_models() -> list[type[Base]]:
    """
    Возвращает список всех классов-моделей,
    зарегистрированных в DeclarativeBase.registry.
    """
    return [mapper.class_ for mapper in Base.registry.mappers]
