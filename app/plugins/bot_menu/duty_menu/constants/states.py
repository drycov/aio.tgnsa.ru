from aiogram.fsm.state import State, StatesGroup


class DutyStates(StatesGroup):
    # Главное меню
    MENU = State()

    # Мои смены
    MY_SHIFTS = State()
    VIEW_SCHEDULE_WEEK = State()
    VIEW_SCHEDULE_MONTH = State()
    REQUEST_SWAP = State()
    CONFIRM_SWAP = State()

    # Команда
    VIEW_TEAM = State()

    # Эскалация / инциденты
    ESCALATION = State()
    REPORT_INCIDENT = State()
    CLOSE_INCIDENT = State()

    # Настройки
    SETTINGS = State()
