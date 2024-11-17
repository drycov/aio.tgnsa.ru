import asyncio
import shutil
from time import time
from typing import Any

import psutil
import redis.asyncio as redis  # Используем асинхронный Redis клиент
from ping3 import ping
from ping3.errors import PingError

from app.utils.logger_instance import app_logger
from config import Config


class Healthy:
    def __init__(self):
        """
        Инициализирует класс Healthy с настройками из Config.
        """

        self.check_interval = Config.HEALTHY_CHECK_INTERVAL  # Интервал проверки
        self.components = {
            "redis": self.check_redis,
            "firebase": self.check_firebase,
            "telegram": self.check_telegram,
            "disk_space": self.check_disk_space,
            "ram": self.check_ram,
            "gateway": self.check_gateway,
            "internet": self.check_internet,
        }
        self.statuses = {}  # Хранение статусов компонентов
        self.redis_client = None
        self.hosts = ["8.8.8.8", "1.1.1.1"]  # Список хостов для проверки
        self.gateway_ip = Config.GATEWAY_IP  # IP-адрес шлюза
        self.start_time = time()  # Время последней проверки redis-компонента

    async def run(self):
        """
        Запускает циклическую проверку состояния компонентов.
        """
        while True:
            await self.perform_health_checks()
            await asyncio.sleep(self.check_interval)

    async def get_component_status(self, name: str) -> dict:
        """
        Возвращает текущий статус указанного компонента.
        """
        if name not in self.components:
            return {"status": "NOT_REGISTERED", "details": f"Компонент {name} не зарегистрирован."}

        try:
            details = await self._run_check(self.components[name])
            return {
                "status": "OK" if details["healthy"] else "FAILED",
                "details": details.get("details", "No additional details"),
                "inform": details.get("inform", False),
                "last_checked": time() - self.start_time,
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "details": str(e),
                "inform": "N/A",
                "last_checked": time() - self.start_time,
            }

    async def generate_report(self) -> dict:
        """
        Формирует подробный отчет о состоянии всех компонентов в формате JSON.
        """
        await self.perform_health_checks()
        # Возвращаем полный отчет в виде словаря
        return {
            "components": {
                name: {
                    "status": status.get("status", "N/A"),
                    "details": status.get("details", "No details available"),
                    "inform": status.get("inform", False),
                    "last_checked": self.statuses[name].get("last_checked", "N/A")
                }
                for name, status in self.statuses.items()
            }
        }

    async def generate_html_report(self) -> str:
        """
        Формирует HTML-отчёт о состоянии всех компонентов.
        """
        await self.perform_health_checks()

        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Health Report</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                h1 { color: #333; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f4f4f4; }
                .ok { color: green; }
                .failed { color: red; }
                .error { color: orange; }
            </style>
            <script>
            // Автоперезагрузка страницы каждые 10 секунд
            setInterval(() => {
                window.location.reload();
            }, 10000);
        </script>
        </head>
        <body>
            <h1>Отчёт о состоянии компонентов</h1>
            <table>
                <thead>
                    <tr>
                        <th>Компонент</th>
                        <th>Статус</th>
                        <th>Детали</th>
                        <th>Информация</th>
                        <th>Последняя проверка</th>

                    </tr>
                </thead>
                <tbody>
        """
        # Заменяем статусы на иконки
        status_icons = {
            "OK": "✅",
            "FAILED": "❌",
            "ERROR": "⚠️",
            "N/A": "❔",
        }

        for name, status in self.statuses.items():
            status_icon = status_icons.get(status.get('status', 'N/A'), "❔")
            last_checked = status.get('last_checked', 'N/A')
            if isinstance(last_checked, (float, int)):
                last_checked = round(last_checked, 2)  # Округляем до 2 знаков
            html += f"""
            <tr>
                <td>{name}</td>
                <td class="{status.get('status', '').lower()}">{status_icon} {status.get('status', 'N/A')}</td>
                <td>{status.get('details', 'No details available')}</td>
                <td>{status.get('inform', 'N/A')}</td>
                <td>{last_checked}</td>

            </tr>
            """
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        return html

    async def perform_health_checks(self):
        """
        Выполняет проверку состояния всех зарегистрированных компонентов.
        """
        for name, check_function in self.components.items():
            try:
                start_time = time()  # Начало проверки
                details = await self._run_check(check_function)
                response_time = time() - start_time
                self.statuses[name] = {
                    "status": "OK" if details["healthy"] else "FAILED",
                    "details": details.get("details", "No additional details"),
                    "inform": details.get("inform", "N/A"),
                    "last_checked": time() - self.start_time,
                }
                app_logger.info(f"Проверка компонента {name}: {self.statuses[name]['status']} "
                                f"за {response_time:.3f} секунд")
            except Exception as e:
                self.statuses[name] = {
                    "status": "ERROR",
                    "details": str(e),
                    "inform": "N/A",
                    "last_checked": time() - self.start_time,
                }
                app_logger.error(f"Ошибка при проверке {name}: {e}")

    async def _run_check(self, check_function):
        """
        Выполняет проверку состояния для асинхронных и синхронных функций.
        """
        return await check_function() if asyncio.iscoroutinefunction(check_function) else check_function()

    async def get_all_statuses(self) -> dict:
        """
        Возвращает текущий статус всех компонентов.
        """
        await self.perform_health_checks()
        # Извлекаем только статус каждого компонента
        return {name: status.get("status", "N/A") for name, status in self.statuses.items()}

    async def initialize_redis(self):
        """
        Инициализирует соединение с Redis.
        """
        try:
            self.redis_client = await redis.from_url(Config.REDIS_URL)
            app_logger.info("Redis клиент успешно инициализирован")
        except Exception as e:
            app_logger.error(f"Ошибка при инициализации Redis клиента: {e}")
            raise

    async def check_hosts(self) -> dict:
        """
        Проверяет доступность хостов через пинг.
        """
        results = {}
        for host in self.hosts:
            try:
                response_time = await self.ping_host(host)
                if response_time:
                    results[host] = {"status": "OK", "inform": f"{response_time:.3f} seconds"}
                else:
                    results[host] = {"status": "FAILED", "details": "Host unreachable"}
            except Exception as e:
                results[host] = {"status": "ERROR", "details": str(e)}

        self.statuses["hosts"] = results
        return results

    async def ping_host(self, host: str) -> Any | None:
        """
        Выполняет пинг указанного хоста.
        :param host: IP-адрес или доменное имя.
        :return: Время отклика (в секундах) или None, если хост недоступен.
        """
        try:
            response_time = await asyncio.to_thread(ping, host, timeout=3)
            return response_time
        except PingError as e:
            app_logger.error(f"Ошибка пинга хоста {host}: {e}")
            return None

    async def check_gateway(self) -> dict:
        """
        Проверяет доступность сетевого шлюза через пинг.
        """
        try:
            response_time = await self.ping_host(self.gateway_ip)
            if response_time:
                return {"healthy": True, "details": f"Шлюз доступен", "inform": f"{response_time:.3f} seconds"}
            return {"healthy": False, "details": "Шлюз недоступен"}
        except Exception as e:
            return {"healthy": False, "details": f"Ошибка проверки шлюза: {e}"}

    async def check_internet(self) -> dict:
        """
        Проверяет доступность интернета через пинг до известных хостов.
        """
        try:
            for host in self.hosts:
                response_time = await self.ping_host(host)
                if response_time:
                    return {"healthy": True,
                            "details": f"Интернет доступен, пинг до {host}: {response_time:.3f} seconds",
                            "inform": f"{response_time:.3f} seconds"}
            return {"healthy": False, "details": "Интернет недоступен (все пинги неудачны)"}
        except Exception as e:
            return {"healthy": False, "details": f"Ошибка проверки доступа в интернет: {e}"}

    async def check_redis(self) -> dict:
        """
        Проверяет доступность Redis через пинг.
        """
        try:
            if not self.redis_client:
                await self.initialize_redis()
            redis_ip = Config.REDIS_HOST  # Укажите IP-адрес Redis-сервера
            response_time = await self.ping_host(redis_ip)
            if response_time:
                return {"healthy": True, "details": f"Redis доступен", "inform": f"{response_time:.3f} seconds"}
            return {"healthy": False, "details": "Redis недоступен (пинг неудачен)"}
        except Exception as e:
            return {"healthy": False, "details": f"Ошибка проверки Redis: {e}"}

    async def check_firebase(self) -> dict:
        """
        Проверяет доступность Firebase через пинг.
        """
        try:
            firebase_host = "firebase.googleapis.com"
            response_time = await self.ping_host(firebase_host)
            if response_time:
                return {"healthy": True, "details": f"Firebase доступен", "inform": f"{response_time:.3f} seconds"}
            return {"healthy": False, "details": "Firebase недоступен (пинг неудачен)"}
        except Exception as e:
            return {"healthy": False, "details": f"Ошибка проверки Firebase: {e}"}

    async def check_telegram(self) -> dict:
        """
        Проверяет доступность серверов Telegram через пинг.
        """
        try:
            telegram_host = "api.telegram.org"
            response_time = await self.ping_host(telegram_host)
            if response_time:
                return {"healthy": True, "details": f"Telegram доступен", "inform": f"{response_time:.3f} seconds"}
            return {"healthy": False, "details": "Telegram недоступен (пинг неудачен)"}
        except Exception as e:
            return {"healthy": False, "details": f"Ошибка проверки Telegram: {e}"}

    def check_disk_space(self) -> dict:
        """
        Проверяет наличие свободного места на диске.
        """
        try:
            _, _, free = shutil.disk_usage("/")
            free_gb = free / (1024 ** 3)
            if free_gb < Config.DISK_SPACE_THRESHOLD_GB:
                return {"healthy": False, "details": f"Мало места на диске",
                        "inform": f"{free_gb:.2f} ГБ"}
            return {"healthy": True, "details": f"Свободно на диске: {free_gb:.2f} ГБ", "inform": f"{free_gb:.2f} ГБ"}
        except Exception as e:
            return {"healthy": False, "details": f"Ошибка при проверке дискового пространства: {e}"}

    def check_ram(self) -> dict:
        """
        Проверяет использование оперативной памяти.
        """
        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024 ** 3)
            available_gb = mem.available / (1024 ** 3)
            used_percent = mem.percent
            if used_percent > Config.RAM_USAGE_THRESHOLD_PERCENT:
                return {"healthy": False,
                        "details": f"Высокое использование RAM: {used_percent}%, доступно {available_gb:.2f} ГБ из {total_gb:.2f} ГБ",
                        "inform": f"{used_percent}%"}
            return {"healthy": True,
                    "details": f"Использование RAM: {used_percent}%, доступно {available_gb:.2f} ГБ из {total_gb:.2f} ГБ",
                    "inform": f"{used_percent}%"}
        except Exception as e:
            return {"healthy": False, "details": f"Ошибка при проверке RAM: {e}"}

    def calculate_system_health(self) -> dict:
        """
        Рассчитывает общее здоровье системы на основе статусов всех компонентов.
        """
        overall_status = "OK"
        failed_components = []
        error_components = []

        for name, status in self.statuses.items():
            if status["status"] == "FAILED":
                overall_status = "FAILED"
                failed_components.append(name)
            elif status["status"] == "ERROR":
                overall_status = "ERROR"
                error_components.append(name)

        # Формируем итоговый результат
        health_report = {
            "system_status": overall_status,
            "failed_components": failed_components,
            "error_components": error_components,
            "details": self.statuses,  # Включаем детализированную информацию о компонентах
        }

        return health_report
