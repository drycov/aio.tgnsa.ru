from enum import Enum


class Symbols(Enum):
    STATUS_CRITICAL = "❗️"  # Критический статус


class Messages(Enum):
    # Сообщения для IP и подсети
    ENTER_IP = "Введите IP-адрес устройства."
    ENTER_SUBNET_P2P = (
        "Введите IP-адрес в формате <i><code>A.B.C.D/Mask(30)</code></i>."
    )
    ENTER_SUBNET = "Введите IP-адрес в формате <i><code>A.B.C.D/Mask(0-32)</code></i>."
    ENTER_24_SUBNET = "Введите IP-адрес в формате <i><code>A.B.C.D/Mask(24)</code></i>."
    SEND_LOCATION = "Отправьте локацию нажав кнопку ниже или поделитесь локацией"

    # Сообщения об ошибках
    ERROR_SUBNET = f"{Symbols.STATUS_CRITICAL.value} Это не CIDR. Укажите IP в формате A.B.C.D / Mask(0 - 32) и повторите."
    ERROR_24_SUBNET = f"{Symbols.STATUS_CRITICAL.value} Это не CIDR. Укажите IP в формате A.B.C.D / Mask(24) и повторите."

    ERROR_P2P = f"{Symbols.STATUS_CRITICAL.value} Это не P2P. Укажите IP в формате A.B.C.D / Mask(30) и повторите."
