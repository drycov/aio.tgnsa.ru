from enum import Enum


class MenuLabels(Enum):
    DEVICE_CHECK = "🧪 Проверка устройства"
    PORT_STATUS = "🌐 Статус портов"
    VLAN_LIST = "📊 Список VLAN"
    DDM_INFO = "ℹ️ Информация DDM"
    CABLE_LENGTH_MEASURE = "📏 Измерение длины кабеля"
    DEVICE_LLDP = "🔗 Информация LLDP"
    DEVICE_MACS = "🖥 MAC-адреса устройств"
