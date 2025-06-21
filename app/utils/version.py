from pathlib import Path
import subprocess
import tomllib  # Python 3.11+
from typing import Optional


def read_version_file(path: Optional[Path] = None) -> Optional[str]:
    """
    Чтение версии из файла VERSION.
    """
    path = path or Path(__file__).resolve().parent.parent.parent / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else None


def read_pyproject_version(path: Optional[Path] = None) -> Optional[str]:
    """
    Попытка извлечения версии из pyproject.toml (poetry или PEP 621).
    """
    path = path or Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    if not path.is_file():
        return None

    try:
        with path.open("rb") as f:
            data = tomllib.load(f)

        return (
            data.get("tool", {}).get("poetry", {}).get("version")
            or data.get("project", {}).get("version")
        )
    except Exception:
        return None


def read_git_tag_version() -> Optional[str]:
    """
    Использование git describe для получения версии по тэгу.
    """
    try:
        return (
            subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"])
            .decode()
            .strip()
        )
    except Exception:
        return None


def resolve_version() -> str:
    """
    Функция разрешения версии с приоритетом:
    1. VERSION
    2. pyproject.toml
    3. git tag
    4. fallback
    """
    return (
        read_version_file()
        or read_pyproject_version()
        or read_git_tag_version()
        or "0.0.0-unknown"
    )


__version__ = resolve_version()
