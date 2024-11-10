from enum import Enum


class Symbols(Enum):
    """
    Перечисление для различных символов, представленных в виде эмодзи, с описанием для каждого символа.
    """

    # Основные статусы соединения
    STATUS_CONNECTED = "✅"  # Соединение установлено
    STATUS_DISCONNECTED = "❌"  # Соединение разорвано
    STATUS_WARNING = "⚠️"  # Предупреждение
    STATUS_CRITICAL = "❗️"  # Критический статус
    STATUS_UNKNOWN = "❓"  # Неизвестный статус
    STATUS_DEAD = "🀄"  # Соединение потеряно
    STATUS_ADMIN_DISABLED = "🅰️"  # Отключено администратором
    STATUS_ADMIN_ENABLED = "✳️"  # Включено администратором
    STATUS_OFFLINE = "🔘"  # Неактивен

    # Статусы и состояние кабеля
    OK = "✅"  # Кабель в норме
    CABLE_CHECKED = "☑️"  # Кабель проверен
    CABLE_CROSSTALK = "🔀"  # Перекрестные помехи
    CABLE_SHORT = "🆘"  # Короткое замыкание
    CABLE_NOT_PRESENT = "✴️"  # Кабель отсутствует
    CABLE_UNKNOWN = "🌀"  # Неизвестный статус кабеля
    CABLE_ABNORMAL = "🆎"  # Ненормальное состояние
    CABLE_DISCONNECTED = "❎"  # Кабель отключен

    # Круговые индикаторы статуса
    INDICATOR_RED = "🔴"  # Красный круг — критический
    INDICATOR_YELLOW = "🟡"  # Желтый круг — предупреждение
    INDICATOR_GREEN = "🟢"  # Зеленый круг — нормально
    INDICATOR_BLUE = "🔵"  # Синий круг
    INDICATOR_BLACK = "⚫️"  # Черный круг
    INDICATOR_PURPLE = "🟣"  # Фиолетовый круг

    # Управление и действия
    ACTION_BACK = "🔙"  # Назад
    ACTION_CONFIRM = "🆗"  # Подтверждение
    ACTION_CANCEL = "🚫"  # Отмена
    ACTION_ERROR = "🛑"  # Ошибка
    ACTION_SEARCH = "🔍"  # Поиск
    ACTION_SETTINGS = "⚙️"  # Настройки
    ACTION_EXIT = "🚪"  # Выход
    ACTION_MAGIC = "🔥"  # Магическое действие

    # Лабораторные и технические обозначения
    TECH_LAB = "🧪"  # Лабораторное тестирование
    TECH_LOCKED = "🔒"  # Заблокировано
    TECH_VLAN = "🔀"  # VLAN
    TECH_DDM = "💥"  # DDM
    TECH_LOG = "📃"  # Журнал событий
    TECH_INCIDENT = "🏴‍☠️"  # Массовый инцидент
    TECH_P2P = "🧬"  # P2P подключение
    TECH_LINK = "🔗"  # Ссылка/связь
    TECH_NETWORK = "🌐"  # Сеть
    TECH_SHIELD = "🛡️"  # Защита
    TECH_MEASURE = "📏"  # Измерение

    # Роли и права доступа
    ROLE_ADMIN = "🏵"  # Администратор
    ROLE_CLI = "📟"  # Командная строка (CLI)
    ROLE_USER = "👤"  # Пользователь
    ROLE_SUPPORT = "🎅"  # Служба поддержки

    # Группы и группы доступа
    GROUP = "📈"  # Основная группа
    GROUP_SECONDARY = "📉"  # Вторая группа
    GROUP_UNKNOWN = "👽"  # Неизвестная группа

    # Разное
    EMOJI_SAND_CLOCK = "⏳"  # Ожидание
    EMOJI_ANNOUNCEMENT = "📢"  # Объявление
    EMOJI_SHARE = "📤"  # Поделиться
    EMOJI_KEY = "🔑"  # Ключ
    EMOJI_LOCK_MANAGER = "🔐"  # Менеджер блокировок
    EMOJI_MAGIC_BALL = "🔮"  # Волшебный шар предсказаний
    EMOJI_DEVICE = "💻"  # Устройство/компьютер
    EMOJI_TOOLS = "🧰"  # Инструменты
    EMOJI_WAVE = "👋"  # Приветствие
    EMOJI_SANTA = "🎅"  # Специальное приветствие
    EMOJI_ALIEN = "👽"  # Иностранный/неизвестный элемент
    EMOJI_FRIENDLY_LINK = "📥"  # Дружественная ссылка
    EMOJI_EDIT = "⌨"  # Рассмотрение