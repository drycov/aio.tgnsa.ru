from enum import Enum
from .symbols import Symbols


class MenuLabels(Enum):
    # Основное меню и навигация
    MAIN_MENU = f"{Symbols.ACTION_MAGIC.value} Главное меню {Symbols.ACTION_MAGIC.value}"
    SETTINGS = f"{Symbols.ACTION_SETTINGS.value} Настройки"
    ADVANCED = f"{Symbols.ACTION_MAGIC.value} Дополнительно"
    BACK = f"{Symbols.ACTION_BACK.value} Назад"
    ENTER = f"{Symbols.INDICATOR_GREEN.value} Войти"
    EXIT = f"{Symbols.INDICATOR_RED.value} Выйти"
    CANCEL = f"{Symbols.ACTION_CANCEL.value} Отмена"
    CONTINUE = f"{Symbols.OK.value} Продолжить"

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
    DUTY_SCHEDULE = f"{Symbols.GROUP.value} График дежурств"
    SERVICE_REQUEST = f"{Symbols.TECH_INCIDENT.value} Запрос на обслуживание"
    MASS_INCIDENT_ALERT = f"{Symbols.EMOJI_MAGIC_BALL.value} Массовый инцидент"
    MASS_MAILING = f"{Symbols.EMOJI_ANNOUNCEMENT.value} Массовая рассылка"

    # Информация о трафике
    TRAFFIC_GRAPH = f"{Symbols.GROUP.value} Трафик на устройстве"
    TRAFFIC_GRAPH_6H = f"{Symbols.GROUP.value} 6 часов"
    TRAFFIC_GRAPH_24H = f"{Symbols.GROUP.value} 1 день"
    TRAFFIC_GRAPH_48H = f"{Symbols.GROUP.value} 2 дня"
    TRAFFIC_GRAPH_1W = f"{Symbols.GROUP.value} Неделя"
    TRAFFIC_GRAPH_1M = f"{Symbols.GROUP.value} Месяц"
    TRAFFIC_GRAPH_3M = f"{Symbols.GROUP.value} Три месяца"
    TRAFFIC_GRAPH_1Y = f"{Symbols.GROUP.value} Год"

    # Приоритеты и уведомления
    PRIORITY_HIGH = f"{Symbols.INDICATOR_RED.value} Высокий приоритет"
    PRIORITY_AVERAGE = f"{Symbols.INDICATOR_YELLOW.value} Средний приоритет"
    PRIORITY_LOW = f"{Symbols.INDICATOR_GREEN.value} Низкий приоритет"
    PRIORITY_INFO = f"{Symbols.INDICATOR_BLUE.value} Информация"
    PRIORITY_ZERO_DAY = f"{Symbols.INDICATOR_BLACK.value} Приоритет нулевого дня"

    # Прочее
    USER_ALLOW = f"{Symbols.OK.value} Добавить пользователя"
    USER_APPROVE = f"{Symbols.CABLE_CHECKED.value} Подтвердить"
    USER_REJECT = f"{Symbols.STATUS_DISCONNECTED.value} Отклонить"
