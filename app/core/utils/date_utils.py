from datetime import datetime, timezone
from typing import Optional

# Форматы временных меток
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'  # С миллисекундами
DATE_FORMAT = '%Y-%m-%d'  # Только дата
TIME_FORMAT = '%H:%M:%S'  # Только время

def isotime(dt: Optional[datetime] = None,
            microseconds: bool = True,
            include_timezone: bool = True) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)  # timezone — импорт из datetime

    if microseconds:
        fmt = '%Y-%m-%dT%H:%M:%S.%f'
        timestamp = dt.strftime(fmt)[:-3]  # Обрезаем до миллисекунд
    else:
        fmt = '%Y-%m-%dT%H:%M:%S'
        timestamp = dt.strftime(fmt)

    if include_timezone:
        timestamp += 'Z'

    return timestamp


def isodate(dt: Optional[datetime] = None) -> str:
    """
    Возвращает дату в формате ISO 8601.

    Args:
        dt (datetime, optional): Объект datetime. По умолчанию datetime.utcnow()

    Returns:
        str: Строка в формате YYYY-MM-DD
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime(DATE_FORMAT)


def isotime_short(dt: Optional[datetime] = None) -> str:
    """
    Возвращает время в формате ISO 8601.

    Args:
        dt (datetime, optional): Объект datetime. По умолчанию datetime.utcnow()

    Returns:
        str: Строка в формате HH:mm:ss
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime(TIME_FORMAT)
