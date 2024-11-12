from calendar import month_name, monthcalendar

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class CalendarMarkup:
    def __init__(self, year: int, month: int):
        self.year = year
        self.month = month

    def create_calendar(self) -> InlineKeyboardMarkup:
        """
        Создает клавиатуру-календарь для выбора даты.
        """
        # Создаем список для строк календаря
        inline_keyboard = []

        # Заголовок с названием месяца и года
        inline_keyboard.append([InlineKeyboardButton(
            text=f"{month_name[self.month]} {self.year}", callback_data="ignore")])

        # Добавляем дни недели
        days_of_week = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        inline_keyboard.append(
            [InlineKeyboardButton(text=day, callback_data="ignore") for day in days_of_week])

        # Дни в месяце
        month_days = monthcalendar(self.year, self.month)
        for week in month_days:
            row = [
                InlineKeyboardButton(
                    text=" " if day == 0 else str(day),
                    callback_data=f"day_{day}_{self.month}_{self.year}" if day != 0 else "ignore"
                )
                for day in week
            ]
            inline_keyboard.append(row)

        # Кнопки "Назад" и "Вперед" для переключения месяцев
        inline_keyboard.append([
            InlineKeyboardButton(text="<", callback_data=f"prev_{self.year}_{self.month}"),
            InlineKeyboardButton(text=">", callback_data=f"next_{self.year}_{self.month}")
        ])

        # Создаем и возвращаем клавиатуру с собранными строками
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard,    resize_keyboard=True,
)

    def navigate_month(self, direction: str):
        """
        Обновляет месяц на следующий или предыдущий в зависимости от direction.
        """
        if direction == "next":
            if self.month == 12:
                self.month = 1
                self.year += 1
            else:
                self.month += 1
        elif direction == "prev":
            if self.month == 1:
                self.month = 12
                self.year -= 1
            else:
                self.month -= 1

    def update_calendar(self, direction: str) -> InlineKeyboardMarkup:
        """
        Обновляет календарь, переключая на следующий или предыдущий месяц.
        """
        self.navigate_month(direction)
        return self.create_calendar()
