from aiogram.fsm.state import StatesGroup, State


class DutyStates(StatesGroup):
    MENU = State()              # Главное меню дежурств
    VIEW_SCHEDULE = State()     # Просмотр своего расписания
    VIEW_TEAM = State()         # Просмотр команды
    REQUEST_SWAP = State()      # Запрос обмена сменой
    CONFIRM_SWAP = State()      # Подтверждение обмена
    REPORT_INCIDENT = State()   # Сообщить об инциденте
    CLOSE_INCIDENT = State()    # Закрыть/подтвердить решение инцидента
