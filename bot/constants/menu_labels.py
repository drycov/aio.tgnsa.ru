"""
This module contains the MenuLabels Enum, which defines various menu labels
and their associated icons or symbols for use in the application.
"""

from enum import Enum


from .symbols import Symbols


class MenuLabels(Enum):
    """
       An enumeration of menu labels with corresponding symbols for UI representation.
       """
    # Основное меню и навигация
    MAIN_MENU = f"{Symbols.EMOJI_MAGIC_BALL.value} Главное меню {Symbols.EMOJI_MAGIC_BALL.value}"
    SETTINGS = f"{Symbols.ACTION_SETTINGS.value} Настройки"
    ADVANCED = f"{Symbols.EMOJI_MAGIC_BALL.value} Дополнительно"
    BACK = f"{Symbols.ACTION_BACK.value} Назад"
    ENTER = f"{Symbols.INDICATOR_GREEN.value} Войти"
    EXIT = f"{Symbols.INDICATOR_RED.value} Выйти"
    CANCEL = f"{Symbols.ACTION_CANCEL.value} Отмена"
    CONTINUE = f"{Symbols.CABLE_OK.value} Продолжить"

    # Пользователи и администрирование
    ADMIN_PANEL = f"{Symbols.EMOJI_TOOLS.value} Администрирование системы"
    SYSTEM_LOGS = f"{Symbols.TECH_LOG.value} Логи системы"
    USER_ADMIN = f"{Symbols.ROLE_USER.value} Пользователи системы"
    NOT_APPROVED_USERS = f"{Symbols.EMOJI_ALIEN.value} Не активированные"
    APPROVED_USERS = f"{Symbols.ROLE_USER.value} Активированные"
    ADMIN_USERS = f"{Symbols.EMOJI_SANTA.value} Администраторы"
    SHARE_CONTACT = f"{Symbols.EMOJI_SHARE.value} Поделиться контактом"

    # Сетевые и диагностические инструменты
    P2P_CALC = f"{Symbols.TECH_P2P.value} Рассчитать P2P-пару"
    CIDR_CALC = f"{Symbols.TECH_NETWORK.value} Расчет сети"
    SUBNET_CALC = f"{Symbols.EMOJI_DEVICE.value} Калькулятор подсети"
    DDM_INFO = f"{Symbols.TECH_DDM.value} DDM информация"
    VLAN_LIST = f"{Symbols.TECH_VLAN.value} Список VLAN"
    PORT_STATUS = f"{Symbols.TECH_LAB.value} Состояние портов"
    CABLE_LENGTH_MEASURE = f"{Symbols.TECH_MEASURE.value} Замер длинны кабеля"
    DEVICE_LLDP = f"{Symbols.TECH_VLAN.value} LLDP Информация"
    PING_DEVICE = f"{Symbols.ROLE_CLI.value} Ping"
    DEVICE_CHECK = f"{Symbols.ACTION_SEARCH.value} Проверить устройство"
    DOF = f"{Symbols.TECH_SHIELD.value} Дежурный сотрудник"
    DUTY_SCHEDULE = f"{Symbols.GROUP_PRIMARY.value} График дежурств"
    DEVICE_MACS = f"{Symbols.EMOJI_DEVICE.value} MAC Таблица"

    SERVICE_REQUEST = f"{Symbols.TECH_INCIDENT.value} Запрос на обслуживание"
    MASS_INCIDENT_ALERT = f"{Symbols.EMOJI_MAGIC_BALL.value} Массовый инцидент"
    MASS_MAILING = f"{Symbols.EMOJI_ANNOUNCEMENT.value} Массовая рассылка"

    # Приоритеты и уведомления
    PRIORITY_HIGH = f"{Symbols.INDICATOR_RED.value} Высокий приоритет"
    PRIORITY_AVERAGE = f"{Symbols.INDICATOR_YELLOW.value} Средний приоритет"
    PRIORITY_LOW = f"{Symbols.INDICATOR_GREEN.value} Низкий приоритет"
    PRIORITY_INFO = f"{Symbols.INDICATOR_BLUE.value} Информация"
    PRIORITY_ZERO_DAY = f"{Symbols.INDICATOR_BLACK.value} Приоритет нулевого дня"

    # Прочее
    USER_ALLOW = f"{Symbols.CABLE_OK.value} Добавить пользователя"
    USER_APPROVE = f"{Symbols.CABLE_CHECKED.value} Подтвердить"
    USER_REJECT = f"{Symbols.STATUS_DISCONNECTED.value} Отклонить"

    # Кнопки для создания и редактирования задачи
    TASK_MANAGER = f"{Symbols.ACTION_TASKS.value} Менеджер задач"
    CREATE_TASK = f"{Symbols.ACTION_ADD.value} Создать задачу"
    VIEW_MY_TASKS = f"{Symbols.ACTION_SEARCH.value} Посмотреть мои задачи"
    VIEW_ALL_TASKS = f"{Symbols.ACTION_SEARCH.value} Посмотреть все задачи"
    VIEW_ASSIGNED_TASKS = f"{Symbols.ACTION_SEARCH.value} Посмотреть задачи"
    HELP_TASKS = f"{Symbols.ACTION_HELP.value} Помощь"

    # Профиль пользователя
    USER_PROFILE = f"{Symbols.ROLE_USER.value} Профиль"
    CHANGE_PASSWORD = f"{Symbols.ACTION_SETTINGS.value} Сменить пароль"

    # Администрирование системы
    ADMIN_SYSTEM = f"{Symbols.EMOJI_SANTA.value} Администрирование системы"
    SYSTEM_INFO = f"{Symbols.TECH_LAB.value} Сведения о системе"
    MONITORING_SYSTEM = f"{Symbols.EMOJI_DEVICE.value} Мониторинг системы"
    SYNC_SYSTEM = f"{Symbols.ACTION_SYNC.value} Синхронизация системы"
    UPGRADE_SYSTEM = f"{Symbols.ACTION_UPGRADE.value} Обновление системы"
    RESET_SYSTEM = f"{Symbols.ACTION_RESET.value} Сброс системы"
    SHUTDOWN_SYSTEM = f"{Symbols.ACTION_POWER.value} Выключение системы"
    VIEW_USERS = f"{Symbols.ACTION_USERS.value} Просмотреть пользователей"
    SEND_BROADCAST = f"{Symbols.ACTION_BROADCAST.value} Отправить рассылку"
    VIEW_LOGS = f"{Symbols.TECH_LOG.value} Просмотреть логи"
    VIEW_STATISTICS = "Просмотреть статистику"
    ERTM_MENU = "📍🛠️ ERTM"

    ERTM_MENU_MESS = "Добро пожаловать в систему ERTM!\nВыберите действие из меню ниже."
    ERTM_ADD_EQUIPMENT = "➕ Добавить оборудование"
    ERTM_LIST_EQUIPMENT = "📋 Список оборудования"
    ERTM_TRACK_EQUIPMENT = "📍 Оборудование по локации"
    ERTM_SCAN_EQUIPMENT = f"{Symbols.ACTION_SEARCH.value} Сканировать"
    ERTM_MANAGE_EQUIPMENT = "⚙️ Управление"
    # Типы оборудования с иконками
    EQ_ANTENNA = "📡 Антенна"
    EQ_ROUTER = "🔌 Маршрутизатор"
    EQ_SERVER = "🖥️ Сервер"
    EQ_OLT = "🔧 OLT"
    EQ_SWITCH = "🔀 Коммутатор"
    EQ_ADSL = "📞 ADSL-модем"

    # Настройки системы
    SYSTEM_SETTINGS = f"{Symbols.ACTION_SETTINGS.value} Настройки системы"


equipment_list = [
    MenuLabels.EQ_ANTENNA.value,
    MenuLabels.EQ_ROUTER,
    MenuLabels.EQ_SERVER.value,
    MenuLabels.EQ_OLT.value,
    MenuLabels.EQ_SWITCH.value,
    MenuLabels.EQ_ADSL.value,
]
