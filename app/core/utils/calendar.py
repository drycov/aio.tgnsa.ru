# app/core/utils/calendar.py
import calendar
from datetime import date, timedelta, datetime
from typing import List, Optional, Set
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.models.duty import DutyShift


def _get_shift_dates(shifts: Optional[List[DutyShift]]) -> Set[str]:
    """Преобразует список смен в множество дат в формате 'YYYY-MM-DD'."""
    if not shifts:
        return set()
    return {s.starts_at.date().isoformat() for s in shifts if s.starts_at}


def build_calendar(
    year: int,
    month: int,
    action: str,
    shifts: Optional[List[DutyShift]] = None,
    tz: str = "UTC",   # <— параметр таймзоны
) -> InlineKeyboardMarkup:
    """
    Генерирует inline-календарь для выбора даты.

    :param year: Год
    :param month: Месяц (1–12)
    :param action: Контекст действия (например, 'my_shifts', 'team', 'swap')
    :param shifts: Список смен (DutyShift), чтобы выделить занятые дни
    :param tz: Строка таймзоны (по умолчанию UTC)
    :return: InlineKeyboardMarkup
    """
    shift_dates = _get_shift_dates(shifts)

    # === Сегодняшняя дата в указанной TZ ===
    today = datetime.now(ZoneInfo(tz)).date()

    # === Заголовок ===
    month_name = date(year, month, 1).strftime("%B %Y")
    header = [InlineKeyboardButton(text=f"📅 {month_name}", callback_data="ignore")]

    # === Дни недели ===
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    week_header = [InlineKeyboardButton(text=day, callback_data="ignore") for day in weekdays]

    # === Календарная сетка ===
    cal = calendar.monthcalendar(year, month)
    calendar_rows = []

    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text="⠀", callback_data="ignore"))
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                day_label = str(day)

                # маркер "сегодня"
                if today == date(year, month, day):
                    day_label = f"[{day_label}]"  # выделим скобками
                    day_label += " 📍"

                # маркеры по сменам
                if date_str in shift_dates:
                    if action == "my_shifts":
                        day_label += " ✅"
                    elif action == "team":
                        day_label += " 👥"
                    elif action == "swap":
                        day_label += " 🔄"
                    else:
                        day_label += " 🟢"

                row.append(
                    InlineKeyboardButton(
                        text=day_label,
                        callback_data=f"{action}_calendar:{date_str}",
                    )
                )
        calendar_rows.append(row)

    # === Навигация ===
    first_day = date(year, month, 1)
    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (first_day + timedelta(days=32)).replace(day=1)

    nav_row = [
        InlineKeyboardButton(
            text="◀️",
            callback_data=f"{action}_prev:{prev_month.year}-{prev_month.month:02d}",
        ),
        InlineKeyboardButton(
            text="▶️",
            callback_data=f"{action}_next:{next_month.year}-{next_month.month:02d}",
        ),
    ]

    keyboard = [header, week_header, *calendar_rows, nav_row]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
