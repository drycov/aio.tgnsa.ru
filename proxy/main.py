import asyncio
import threading
from cli.shell import AsyncProxyAdminShell
from proxy.config import logger
from server.vpn_server import start_vpn_server

stop_event = threading.Event()


async def run_vpn_server_async():
    """Асинхронная обертка для запуска VPN-сервера с поддержкой завершения."""
    try:
        await start_vpn_server()
    except asyncio.CancelledError:
        logger.info("Асинхронный VPN-сервер остановлен.")
    except Exception as e:
        logger.error(f"Ошибка VPN-сервера: {e}")


def run_vpn_server():
    """Функция для запуска VPN-сервера в отдельном потоке."""
    logger.info("VPN-сервер запущен в отдельном потоке.")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    vpn_task = loop.create_task(run_vpn_server_async())

    try:
        while not stop_event.is_set():
            loop.run_until_complete(asyncio.sleep(1))
    finally:
        vpn_task.cancel()  # Отмена задачи сервера
        loop.run_until_complete(vpn_task)  # Дождаться завершения задачи
        loop.close()
        logger.info("VPN-сервер остановлен.")



async def main():
    """Главная точка входа."""
    # Запуск VPN-сервера в отдельном потоке
    vpn_thread = threading.Thread(target=run_vpn_server, daemon=True)
    vpn_thread.start()
    logger.info("VPN-сервер запущен в отдельном потоке.")

    # Запуск CLI
    shell = AsyncProxyAdminShell()
    try:
        await shell.cmdloop()
    except KeyboardInterrupt:
        logger.info("CLI завершён пользователем.")
    finally:
        logger.info("Завершение программы.")
        stop_event.set()  # Установить флаг завершения
        vpn_thread.join()  # Ожидание завершения потока


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("VPN-сервер остановлен пользователем.")
