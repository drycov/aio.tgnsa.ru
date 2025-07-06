from enum import Enum

class Symbols(Enum):
    STATUS_OK = "🟢"  # Успешно / готово
    STATUS_FAIL = "🔴"  # Ошибка / сбой
    STATUS_WARNING = "⚠️"  # Предупреждение
    STATUS_ERROR = "❗"  # Критическая ошибка
    STATUS_HOURGLASS = "⏳"  # Ожидание / процесс
    STATUS_SUCCESS = "✅"  # Успешно завершено (альтернатива)
    STATUS_FAIL_ALT = "❎"  # Ошибка (альтернативный символ)
    STATUS_NO = "🚫"  # Нет / запрещено
    STATUS_STOP = "⛔️"  # Стоп / запрещено"
        # ========== INTERFACE (Физические интерфейсы) ==========
    INTERFACE_PORT = "🔌"  # Интерфейс / порт
    INTERFACE_OPER_UP = "🟢"  # Оперативный статус: включен
    INTERFACE_OPER_DOWN = "🔴"  # Оперативный статус: выключен
    INTERFACE_ADMIN_UP = "🟡"  # Административный статус: включен
    INTERFACE_ADMIN_DOWN = "⚫️"  # Административный статус: выключен

    # ========== CABLE (Кабель и физический уровень) ==========
    CABLE_OK = "✅"  # Кабель подключен и работает
    CABLE_UNPLUGGED = "❌"  # Кабель не подключен
    CABLE_FAULT = "⚠️"  # Неисправность кабеля (короткое, обрыв)
    CABLE_TESTING = "🔌🧪"  # Тестирование кабеля
    CABLE_UNKNOWN = "🔌❓"  # Статус кабеля неизвестен
    CABLE_CROSSTALK = "🔌🔁"  # Помехи / наводки
    CABLE_LOOP = "🔁🔌"  # Петля кабеля (loopback)

class MenuLabels(Enum):
    DEVICE_CHECK = "🧪 Проверка устройства"
    PORT_STATUS = "🌐 Статус портов"
    VLAN_LIST = "📊 Список VLAN"
    DDM_INFO = "ℹ️ Информация DDM"
    CABLE_LENGTH_MEASURE = "📏 Измерение длины кабеля"
    DEVICE_LLDP = "🔗 Информация LLDP"
    DEVICE_MACS = "🖥 MAC-адреса устройств"
    PPAGE = "⬅️"
    NPAGE = "➡️"
