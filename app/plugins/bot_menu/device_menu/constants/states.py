from aiogram.fsm.state import StatesGroup, State


# Команды для работы с устройствами
class DeviceCommands(StatesGroup):
    MENU = State()  # Главное меню команд устройства
    CHECK_STATUS = State()
    PORT_INFORMATION = State()
    VLAN_INFORMATION = State()
    DDM_INFORMATION = State()
    CABLE_MEASUREMENT = State()
    LLDP_INFORMATION = State()
