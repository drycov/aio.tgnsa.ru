from pathlib import Path
import subprocess
import tomllib  # Python 3.11+
from typing import Optional
from loguru import logger as loguru_logger

# Определяем BASE_DIR независимо
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def read_version_file(path: Optional[Path] = None) -> Optional[str]:
    """
    Читает версию из файла VERSION, если он существует.

    Args:
        path (Optional[Path]): Путь к файлу VERSION. По умолчанию ищется в корне проекта.

    Returns:
        Optional[str]: Строка с версией, если файл найден и прочитан; иначе None.
    """
    path = path or BASE_DIR / "VERSION"
    loguru_logger.debug(f"[version] Чтение версии из {path}")
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() if path.is_file() else None
    except Exception as e:
        loguru_logger.error(f"[version] Ошибка чтения VERSION: {e}")
        return None


def read_pyproject_version(path: Optional[Path] = None) -> Optional[str]:
    """
    Извлекает версию из pyproject.toml (Poetry/PEP 621).

    Args:
        path (Optional[Path]): Путь к pyproject.toml. По умолчанию ищется в корне проекта.

    Returns:
        Optional[str]: Версия проекта из pyproject.toml, если найдена; иначе None.
    """
    path = path or BASE_DIR / "pyproject.toml"
    loguru_logger.info(f"[version] Чтение версии из {path}")

    if not path.is_file():
        return None
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        return (
            data.get("tool", {}).get("poetry", {}).get("version")
            or data.get("project", {}).get("version")
        )
    except Exception as e:
        loguru_logger.error(f"[version] Ошибка чтения pyproject.toml: {e}")
        return None


def read_git_tag_version() -> Optional[str]:
    """
    Получает версию из Git (тег или короткий hash).

    Поведение:
        - Если присутствует хотя бы один тег — возвращается результат `git describe --tags`
        - Если тегов нет — возвращается `no-tags-<short-commit>`
        - При любой ошибке возвращается None

    Returns:
        Optional[str]: Версия из Git или fallback-значение `no-tags-<short-hash>`, либо None.
    """
    try:
        # Проверяем, что git установлен
        subprocess.run(
            ["git", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        tags_exist = subprocess.run(
            ["git", "tag"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        ).stdout.strip()

        if tags_exist:
            return (
                subprocess.check_output(["git", "describe", "--tags"])
                .decode("utf-8")
                .strip()
            )
        else:
            commit_hash = (
                subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
                .decode("utf-8")
                .strip()
            )
            return f"no-tags-{commit_hash}"
    except Exception as e:
        loguru_logger.error(f"[version] Ошибка получения версии из git: {e}")
        return None


def resolve_version() -> str:
    """
    Последовательное разрешение версии проекта по приоритету:

    1. Чтение из файла VERSION
    2. Извлечение из pyproject.toml
    3. Определение из Git (тег или hash fallback)
    4. Статическое значение по умолчанию "0.0.0-unknown"

    Returns:
        str: Определённая версия проекта.
    """
    return (
        read_version_file()
        or read_pyproject_version()
        or read_git_tag_version()
        or "0.0.0-unknown"
    )


__version__ = resolve_version()
