from aiogram.fsm.state import StatesGroup, State


class DeviceCommands(StatesGroup):
    """
    FSM-группа для управления командами устройств.
    Определяет сценарий взаимодействия пользователя с ботом.
    """

    # Главное меню
    MENU = State()

    # Базовая диагностика
    CHECK_STATUS = State()       # Проверка доступности устройства
    PORT_INFORMATION = State()   # Информация о портах
    VLAN_INFORMATION = State()   # Информация о VLAN

    # Расширенная диагностика
    DDM_INFORMATION = State()    # Диагностика DDM (SFP-модули)
    CABLE_MEASUREMENT = State()  # Измерение кабеля (TDR, длина, обрыв)
    LLDP_INFORMATION = State()   # Информация по LLDP соседям

    # Общие состояния
    UNKNOWN = State()            # Неизвестная команда / fallback
    ERROR = State()              # Ошибка в обработке команды
