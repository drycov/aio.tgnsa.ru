import asyncio
import ssl
from datetime import datetime
from proxy.config import logger, SERVER_IP, SERVER_PORT, CERT_FILE, KEY_FILE, REMOTE_SERVER_IP, REMOTE_SERVER_PORT
from proxy.core import is_authorized
from proxy.server.ssl_manager import validate_ssl_certificates, generate_ssl_certificates

active_connections = 0

async def parse_http_request(data):
    """
    Парсинг HTTP-запроса.
    :param data: Данные запроса в виде bytes.
    :return: Метод, путь, версия HTTP, заголовки.
    """
    try:
        lines = data.decode("utf-8").split("\r\n")  # Разделяем строки
        request_line = lines[0].split(" ")  # Первая строка содержит метод, путь и версию
        method, path, version = request_line

        headers = {}
        for line in lines[1:]:  # Пропускаем первую строку
            if ": " in line:  # Заголовки имеют формат "Ключ: Значение"
                key, value = line.split(": ", 1)
                headers[key.strip()] = value.strip()

        return method, path, version, headers
    except Exception as e:
        raise ValueError(f"Ошибка парсинга HTTP-запроса: {e}")


async def forward_data(source, destination):
    """Перенаправление данных между источником и получателем."""
    try:
        while True:
            data = await source.read(65536)  # Читаем данные порциями
            if not data:
                break
            destination.write(data)  # Пересылаем данные
            await destination.drain()
    except Exception as e:
        logger.error(f"Ошибка при перенаправлении данных: {e}")


async def handle_client(reader, writer):
    """Обработка подключения клиента."""
    global active_connections
    addr = writer.get_extra_info("peername")
    active_connections += 1
    logger.info(f"Новое подключение от {addr}. Активных соединений: {active_connections}")

    try:
        # Читаем первый запрос клиента
        client_request = await reader.read(65536)
        if not client_request:
            logger.warning("Пустой запрос от клиента.")
            return

        # Парсим заголовки
        method, path, version, headers = await parse_http_request(client_request)

        # Проверка авторизации
        if not await is_authorized(headers):
            response = (
                "HTTP/1.1 401 Unauthorized\r\n"
                "Content-Length: 0\r\n\r\n"
            ).encode()
            writer.write(response)
            await writer.drain()
            logger.warning(f"Неавторизованный доступ от {addr}")
            return

        # Устанавливаем соединение с удалённым сервером
        remote_reader, remote_writer = await asyncio.open_connection(REMOTE_SERVER_IP, REMOTE_SERVER_PORT)
        logger.info(f"Подключение к {REMOTE_SERVER_IP}:{REMOTE_SERVER_PORT} установлено.")

        # Отправляем запрос на удалённый сервер
        remote_writer.write(client_request)
        await remote_writer.drain()

        # Перенаправляем ответ от удалённого сервера клиенту
        await forward_data(remote_reader, writer)

        # Закрываем соединение с удалённым сервером
        remote_writer.close()
        await remote_writer.wait_closed()
    except ConnectionResetError:
        logger.warning(f"Клиент {addr} разорвал соединение.")
    except Exception as e:
        logger.error(f"Ошибка обработки клиента {addr}: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.warning(f"Ошибка при закрытии соединения с {addr}: {e}")
        active_connections -= 1
        logger.info(f"Соединение с {addr} закрыто. Активных соединений: {active_connections}")


async def monitor_server(interval=10):
    """Мониторинг состояния сервера."""
    while True:
        logger.info(f"[Мониторинг]: Активных соединений: {active_connections}. Время: {datetime.now()}")
        await asyncio.sleep(interval)


async def start_vpn_server(host=SERVER_IP, port=SERVER_PORT):
    """Запуск VPN-сервера."""
    try:
        if not validate_ssl_certificates():
            generate_ssl_certificates()

        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=str(CERT_FILE), keyfile=str(KEY_FILE))

        server = await asyncio.start_server(handle_client, host, port, ssl=ssl_context)
        addr = server.sockets[0].getsockname()
        logger.info(f"VPN-сервер запущен на {addr}")

        # Запуск сервера и мониторинга параллельно
        await asyncio.gather(
            server.serve_forever(),
            monitor_server()
        )
    except Exception as e:
        logger.exception(f"Ошибка запуска VPN-сервера: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(start_vpn_server())
    except KeyboardInterrupt:
        logger.info("VPN-сервер остановлен пользователем.")
