from enum import Enum


class NetworkMessages(Enum):
    ERROR_SUBNET_CALCULATION = "Ошибка в вычислении подсети: {error}"
    ERROR_P2P_CALCULATION = "Ошибка в вычислении P2P: {error}"
    ERROR_PING = "Ошибка при выполнении ping: {error}"
    ERROR_FILE_READ = "Ошибка при чтении файла {file_path}: {error}"
    ERROR_SUBNET_FORMAT = "Ошибка в формате адреса сети."
    ERROR_P2P_FORMAT = "Ошибка в формате P2P адреса."
    ERROR_IP_MESSAGE = (
        "🆘 Некорректный IP-адрес. Укажите IP в формате A.B.C.D и повторите."
    )
