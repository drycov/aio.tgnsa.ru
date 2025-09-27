from enum import Enum


class Symbols(str, Enum):
    """Набор стандартных символов-эмодзи для статусов."""
    OK = "✅"
    FAIL = "❌"
    WARN = "⚠️"
    INFO = "ℹ️"
    CLOCK = "⏱"
    GEAR = "⚙️"


class Messages(str, Enum):
    """Шаблоны сообщений для взаимодействия с пользователем."""

    ENTER_IP = "Введите IP-адрес устройства."

    DEVICE_INFO = (
        "{status} Статус устройства: {availability}\n"
        "🌐 IP устройства: {host}\n"
        "🏭 Производитель: {vendor}\n"
        "💻 Имя устройства: {sw_sys_name}\n"
        "📦 Модель устройства: {sw_model}\n"
        "📍 Address: {address}\n"
        "⏱ UpTime: {sw_up_time} ({up_time})\n"
    )

    ERROR_GENERIC = (
        f"{Symbols.FAIL.value} Ошибка при обработке запроса. Попробуйте позже."
    )

    DEVICE_NOT_FOUND = (
        f"{Symbols.FAIL.value} Устройство с указанным IP не найдено."
    )

    DEVICE_UNAVAILABLE = (
        f"{Symbols.WARN.value} Устройство {Symbols.FAIL.value} недоступно."
    )
