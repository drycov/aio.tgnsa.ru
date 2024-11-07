from aiogram.fsm.state import StatesGroup, State


# Форма регистрации пользователя
class RegistrationForm(StatesGroup):
    first_name = State()
    last_name = State()
    company_post = State()
    phone_number = State()
    email = State()
    confirmation = State()


# Основные команды
class MainCommands(StatesGroup):
    START = State()
    MAIN_MENU = State()  # Ясность в названии
    ADMIN_PANEL = State()  # Ясное название для раздела администрирования


# Продвинутые команды
class AdvancedCommands(StatesGroup):
    MENU = State()  # Главное меню продвинутых команд
    CIDR_CALCULATOR = State()
    P2P_CALCULATOR = State()
    DEVICE_PING = State()
    MASS_INCIDENT = State()
    API_TOKEN_GENERATOR = State()


# Команды для работы с устройствами
class DeviceCommands(StatesGroup):
    MENU = State()  # Главное меню команд устройства
    CHECK_STATUS = State()
    PORT_INFORMATION = State()
    VLAN_INFORMATION = State()
    DDM_INFORMATION = State()
    CABLE_MEASUREMENT = State()
    LLDP_INFORMATION = State()
