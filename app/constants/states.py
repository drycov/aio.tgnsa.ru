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
    SYSTEM_MENU = State()
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


class TaskCreationState(StatesGroup):
    TASK_MENU = State()  # Состояние для главного меню создания задачи
    DATE = State()  # Состояние для выбора даты задачи
    END_DATE = State()  # Состояние для выбора даты окончания задачи
    TITLE = State()  # Состояние для ввода названия задачи
    DESCRIPTION = State()  # Состояние для ввода описания задачи
    PRIORITY = State()  # Состояние для выбора приоритета задачи
    EMPLOYEE = State()  # Состояние для выбора сотрудника
    CONFIRMATION = State()  # Состояние для подтверждения задачи (если требуется)

class TaskPaginationState(StatesGroup):
    viewing_tasks = State()  # Состояние для отображения задач
    user_role = State()      # Состояние для хранения роли пользователя (создатель или исполнитель)

class ERTMManager(StatesGroup):
    ERTM_MENU = State()
    TRACK_EQ = State()
    EQ_SCAN = State()

# Кортеж со всеми состояниями
ALL_STATES = (
    # Состояния RegistrationForm
    RegistrationForm.first_name, RegistrationForm.last_name, RegistrationForm.company_post,
    RegistrationForm.phone_number, RegistrationForm.email, RegistrationForm.confirmation,

    # Состояния MainCommands
    MainCommands.START, MainCommands.MAIN_MENU, MainCommands.ADMIN_PANEL,

    # Состояния AdvancedCommands
    AdvancedCommands.MENU, AdvancedCommands.CIDR_CALCULATOR, AdvancedCommands.P2P_CALCULATOR,
    AdvancedCommands.DEVICE_PING, AdvancedCommands.MASS_INCIDENT, AdvancedCommands.API_TOKEN_GENERATOR,

    # Состояния DeviceCommands
    DeviceCommands.MENU, DeviceCommands.CHECK_STATUS, DeviceCommands.PORT_INFORMATION,
    DeviceCommands.VLAN_INFORMATION, DeviceCommands.DDM_INFORMATION, DeviceCommands.CABLE_MEASUREMENT,
    DeviceCommands.LLDP_INFORMATION,

    # Состояния TaskCreationState
    TaskCreationState.DATE, TaskCreationState.PRIORITY, TaskCreationState.EMPLOYEE, TaskCreationState.CONFIRMATION,TaskCreationState.TASK_MENU
)
