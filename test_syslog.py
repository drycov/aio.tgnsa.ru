import logging
import socket
import time
from logging.handlers import SysLogHandler


def setup_logger():
    # Создаем базовый логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Настройка обработчика для отправки сообщений на локальный Syslog сервер через UDP
    syslog_handler = SysLogHandler(address=('127.0.0.1', 514), socktype=socket.SOCK_DGRAM)

    # Устанавливаем формат сообщений
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    syslog_handler.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    logger.addHandler(syslog_handler)
    return logger


def main():
    # Настройка логгера
    logger = setup_logger()

    # Бесконечный цикл отправки сообщений
    while True:
        logger.info("Test syslog message from Python")
        time.sleep(10)  # Пауза между отправками, можно изменить время


if __name__ == "__main__":
    main()
