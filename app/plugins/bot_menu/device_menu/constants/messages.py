from enum import Enum

class Symbols(Enum):
    OK = "✅"


class Messages(Enum):
    ENTER_IP = "Введите IP-адрес устройства."
    DEVICE_INFO = (
        f"Статус устройства:{Symbols.OK.value} Доступен\n"
        "IP устройства: {host}\n"
        "Производитель: {vendor}\n"
        "Имя устройства: {sw_sys_name}\n"
        "Модель устройства: {sw_model}\n"
        "Address: {address}\n"
        "UpTime: {sw_up_time}({up_time})\n"
    )