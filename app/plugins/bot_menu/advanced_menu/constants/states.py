from aiogram.fsm.state import StatesGroup, State


# Основные команды
class Advanced(StatesGroup):
    MENU = State()  # Главное меню продвинутых команд
    CIDR_CALCULATOR = State()
    P2P_CALCULATOR = State()
    DEVICE_PING = State()
    MASS_INCIDENT = State()
    API_TOKEN_GENERATOR = State()
