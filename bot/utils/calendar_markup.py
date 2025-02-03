# -*- coding: utf-8 -*-

from calendar import monthcalendar
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Константы для месяцев и дней недели
MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]
DAYS_OF_WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

class CalendarMarkup:
    def __init__(self, year: int, month: int):
        """
        Инициализация класса календаря с заданным годом и месяцем.

        :param year: Год для отображения.
        :param month: Месяц для отображения (от 1 до 12).
        """
        self.year = year
        self.month = month

    def create_calendar(self) -> InlineKeyboardMarkup:
        """
        Создает клавиатуру-календарь для выбора даты.

        :return: InlineKeyboardMarkup с календарем.
        """
        inline_keyboard = []

        # Заголовок с названием месяца и года
        inline_keyboard.append([InlineKeyboardButton(
            text=f"{MONTHS[self.month - 1]} {self.year}", callback_data="ignore")])

        # Добавляем дни недели
        inline_keyboard.append([
            InlineKeyboardButton(text=day, callback_data="ignore") for day in DAYS_OF_WEEK
        ])

        # Дни в месяце
        month_days = monthcalendar(self.year, self.month)
        for week in month_days:
            row = [
                InlineKeyboardButton(
                    text=str(day) if day != 0 else " ",  # Пустое место для дня 0
                    callback_data=f"day_{day}_{self.month}_{self.year}" if day != 0 else "ignore"
                ) for day in week
            ]
            inline_keyboard.append(row)

        # Кнопки для навигации по месяцам
        inline_keyboard.append([
            InlineKeyboardButton(text="<", callback_data=f"prev_{self.year}_{self.month}"),
            InlineKeyboardButton(text=">", callback_data=f"next_{self.year}_{self.month}")
        ])

        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, resize_keyboard=True)

    def navigate_month(self, direction: str):
        """
        Переключает месяц в зависимости от направления.
        Если месяц невалиден, то не меняет месяц и год.

        :param direction: Направление для навигации ('next' или 'prev').
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

        :param direction: Направление для навигации ('next' или 'prev').
        :return: Новый календарь с обновленными данными.
        """
        self.navigate_month(direction)
        return self.create_calendar()
