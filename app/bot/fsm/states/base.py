from aiogram.fsm.state import StatesGroup, State


# Основные команды
class CMDState(StatesGroup):
    CMD_START = State()
    CMD_HELP = State()
    CMD_SETTINGS = State()
    CMD_PROFILE = State()
