from enum import Enum


class DutySymbols(str, Enum):
    DUTY = "📅"
    SHIFT = "👨‍💻"
    TEAM = "👥"
    ESCALATION = "⚡"
    BACK = "⬅️"
    SETTINGS = "⚙️"
    INCIDENT = "🚨"
    SWAP = "🔄"
    SUCCESS = "✅"
    FAIL = "❌"
    INFO = "ℹ️"


class DutyMenuLabels(str, Enum):
    # Главное меню
    MAIN = f"{DutySymbols.DUTY.value} Дежурства"
    MY_SHIFTS = f"{DutySymbols.SHIFT.value} Мои смены"
    TEAM_SCHEDULE = f"{DutySymbols.TEAM.value} Расписание команды"
    ESCALATION = f"{DutySymbols.ESCALATION.value} Эскалация"
    SETTINGS = f"{DutySymbols.SETTINGS.value} Настройки"
    BACK = f"{DutySymbols.BACK.value} Назад"

    # Подменю "Мои смены"
    VIEW_WEEK = f"{DutySymbols.INFO.value} Смены на неделю"
    VIEW_MONTH = f"{DutySymbols.INFO.value} Смены на месяц"
    REQUEST_SWAP = f"{DutySymbols.SWAP.value} Обмен сменой"
    CONFIRM_SWAP = f"{DutySymbols.SUCCESS.value} Подтвердить обмен"

    # Подменю "Команда"
    VIEW_TEAM = f"{DutySymbols.INFO.value} Просмотр команды"

    # Подменю "Эскалация / инциденты"
    REPORT_INCIDENT = f"{DutySymbols.INCIDENT.value} Сообщить об инциденте"
    CLOSE_INCIDENT = f"{DutySymbols.SUCCESS.value} Закрыть инцидент"

    # Подменю "Настройки"
    CHANGE_SETTINGS = f"{DutySymbols.SETTINGS.value} Изменить параметры"

    def __str__(self) -> str:
        return self.value


DUTY_MENU_STRUCTURE = {
    # Главное меню
    "main": [
        DutyMenuLabels.MY_SHIFTS,
        DutyMenuLabels.TEAM_SCHEDULE,
                DutyMenuLabels.BACK,

    ],

    # Мои смены
    "my_shifts": [
        DutyMenuLabels.VIEW_WEEK,
        DutyMenuLabels.VIEW_MONTH,
        DutyMenuLabels.REQUEST_SWAP,
        DutyMenuLabels.CONFIRM_SWAP,
        DutyMenuLabels.BACK,
    ],

    # Команда
    "team_schedule": [
        DutyMenuLabels.VIEW_TEAM,
        DutyMenuLabels.BACK,
    ],


}
