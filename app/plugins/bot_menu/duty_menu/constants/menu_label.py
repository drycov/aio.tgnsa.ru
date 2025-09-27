from enum import Enum


class DutySymbols(Enum):
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


class DutyMenuLabels(Enum):
    MAIN = f"{DutySymbols.DUTY.value} Дежурства"
    MY_SHIFTS = f"{DutySymbols.SHIFT.value} Мои смены"
    TEAM_SCHEDULE = f"{DutySymbols.TEAM.value} Расписание команды"
    ESCALATION = f"{DutySymbols.ESCALATION.value} Эскалация"
    SETTINGS = f"{DutySymbols.SETTINGS.value} Настройки"
    BACK = f"{DutySymbols.BACK.value} Назад"

    def __str__(self) -> str:
        return self.value
    

DUTY_MENU_STRUCTURE = {
    "main": [
        DutyMenuLabels.MY_SHIFTS,
        DutyMenuLabels.TEAM_SCHEDULE,
        DutyMenuLabels.ESCALATION,
        DutyMenuLabels.SETTINGS,
        DutyMenuLabels.BACK,
    ]
}
