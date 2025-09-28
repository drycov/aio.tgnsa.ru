from enum import Enum


class NetworkMessages(Enum):
    """
    Перечисление шаблонов сообщений об ошибках при сетевых операциях.

    Используется для стандартизации и интернационализации вывода ошибок.
    Метод format позволяет подставлять динамические параметры.
    """

    ERROR_SUBNET_CALCULATION = "Ошибка в вычислении подсети: {error}"
    ERROR_P2P_CALCULATION = "Ошибка в вычислении P2P: {error}"
    ERROR_PING = "Ошибка при выполнении ping: {error}"
    ERROR_FILE_READ = "Ошибка при чтении файла {file_path}: {error}"
    ERROR_SUBNET_FORMAT = "Ошибка в формате адреса сети."
    ERROR_P2P_FORMAT = "Ошибка в формате P2P адреса."
    ERROR_IP_MESSAGE = (
        "🆘 Некорректный IP-адрес. Укажите IP в формате A.B.C.D и повторите."
    )

    def format(self, **kwargs) -> str:
        """
        Форматирует сообщение, подставляя значения в шаблон.

        :param kwargs: именованные параметры, соответствующие плейсхолдерам в шаблоне.
        :return: строка с готовым сообщением.
        """
        return self.value.format(**kwargs)
