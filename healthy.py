import asyncio
import shutil
from time import time
from typing import Union

import psutil
import redis.asyncio as redis
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ping3 import ping
from ping3.errors import PingError

from app.utils.logger_instance import app_logger
from config import Config


class Healthy:
    """
    Класс для управления проверкой состояния системы и расписанием задач.
    """

    status_icons = {
        "OK": "✅",
        "FAILED": "❌",
        "ERROR": "⚠️",
        "N/A": "❔",
    }

    def __init__(self):
        """
        Инициализация менеджера состояния системы.
        """
        self.scheduler = AsyncIOScheduler()
        self.check_interval = Config.HEALTHY_CHECK_INTERVAL
        self.statuses = {}
        self.start_time = time()
        self.redis_client = None
        self.hosts = ["8.8.8.8", "1.1.1.1"]
        self.gateway_ip = Config.GATEWAY_IP
        self.firebase_host = "firebase.googleapis.com"
        self.telegram_host = "api.telegram.org"

        # Компоненты и их функции проверки
        self.components = {
            "redis": self.check_redis,
            "firebase": self._make_async_check(self.firebase_host, "Firebase"),
            "telegram": self._make_async_check(self.telegram_host, "Telegram"),
            "disk_space": self.check_disk_space,
            "ram": self.check_ram,
            "gateway": self._make_async_check(self.gateway_ip, "Шлюз"),
            "internet": self.check_internet,
        }

        # Заголовки и подсказки для компонентов
        self.titles = {
            "redis": "Redis",
            "firebase": "Firebase",
            "telegram": "Telegram",
            "disk_space": "Дисковое пространство",
            "ram": "Оперативная память",
            "gateway": f"Шлюз {Config.GATEWAY_IP}",
            "internet": "Интернет",
        }
        self.component_tooltips = {
            "redis": "Проверка доступности кэша Redis",
            "firebase": "Доступ к Firebase",
            "telegram": "Подключение к Telegram Bot API",
            "disk_space": "Проверка свободного места на диске",
            "ram": "Проверка доступной оперативной памяти",
            "gateway": "Проверка статуса сетевого шлюза",
            "internet": "Проверка подключения к интернету",
        }

        # Планировщик задач
        self.jobs = {
            "health_check": self._schedule_task("health_check", self.perform_health_checks, self.check_interval),
            "redis_reconnect": self._schedule_task("redis_reconnect", self.initialize_redis, 600),
        }

    def _make_async_check(self, host: str, name: str):
        """
        Создает функцию для проверки сетевого компонента.
        """

        async def check():
            return await self.check_network_component(host, name)

        return check

    def _schedule_task(self, job_name: str, func, interval: int):
        """
        Создаёт задачу в планировщике.
        """
        try:
            self.scheduler.add_job(
                func,
                trigger=IntervalTrigger(seconds=interval),
                id=job_name,
                replace_existing=True
            )
            return self.scheduler.get_job(job_name)
        except Exception as e:
            app_logger.error(f"Ошибка при добавлении задачи '{job_name}': {e}")
            return None

    def start_scheduler(self):
        """
        Запускает планировщик задач.
        """
        if not self.scheduler.running:
            self.scheduler.start()
            app_logger.info("Планировщик задач успешно запущен.")

    def stop_scheduler(self):
        """
        Останавливает планировщик задач.
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            app_logger.info("Планировщик задач успешно остановлен.")

    def get_scheduler_status(self, job_id: str) -> dict:
        """
        Получает статус задачи по идентификатору.
        :param job_id: Идентификатор задачи в планировщике.
        :return: Статус задачи (словарь с информацией или сообщение об ошибке).
        """
        try:
            job: Job = self.scheduler.get_job(job_id)
            if not job:
                return {"status": "NOT_FOUND", "details": f"Задача с ID '{job_id}' не найдена."}

            return {
                "status": "RUNNING" if job.next_run_time else "PAUSED",
                "id": job.id,
                "next_run_time": job.next_run_time,
            }
        except Exception as e:
            app_logger.error(f"Ошибка при получении статуса задачи '{job_id}': {e}")
            return {"status": "ERROR", "details": str(e)}

    def get_all_scheduler_statuses(self) -> dict:
        """
        Получает статус всех задач в планировщике.
        :return: Словарь со статусами задач.
        """
        try:
            jobs = self.scheduler.get_jobs()
            return {
                job.id: {
                    "status": "RUNNING" if job.next_run_time else "PAUSED",
                    "next_run_time": job.next_run_time,
                }
                for job in jobs
            }
        except Exception as e:
            app_logger.error(f"Ошибка при получении статусов задач: {e}")
            return {"status": "ERROR", "details": str(e)}

    async def perform_health_checks(self):
        """
        Выполняет детализированную проверку состояния всех компонентов.
        """
        try:
            for name, check_function in self.components.items():
                start_time = time()  # Записываем время начала проверки
                details = await check_function() if asyncio.iscoroutinefunction(check_function) else check_function()
                response_time = time() - start_time  # Вычисляем время выполнения проверки

                # Сохраняем результат проверки
                self.statuses[name] = {
                    "title": self.titles.get(name, "N/A"),
                    "tooltip": self.component_tooltips.get(name, "Описание отсутствует"),
                    "status": "OK" if details.get("healthy") else "FAILED",
                    "details": details.get("details", "No details available"),
                    "inform": details.get("inform", "N/A"),
                    "last_checked": round(response_time, 2),  # Время выполнения в секундах
                }
        except Exception as e:
            app_logger.error(f"Ошибка при выполнении детализированной проверки: {e}")
            raise

    def _update_status(self, name: str, details: dict, response_time: Union[float, str], is_error=False):
        """
        Обновляет статус компонента в словаре состояний.
        """
        self.statuses[name] = {
            "title": self.titles.get(name, "N/A"),
            "tooltip": self.component_tooltips.get(name, "Описание отсутствует"),
            "status": "ERROR" if is_error else ("OK" if details.get("healthy") else "FAILED"),
            "details": details.get("details", "No additional details"),
            "inform": details.get("inform", "N/A"),
            "last_checked": response_time,
        }

    async def check_redis(self) -> dict:
        """
        Проверяет доступность Redis.
        """
        try:
            if not self.redis_client:
                await self.initialize_redis()
            response_time = await self.ping_host(Config.REDIS_HOST)
            return {"healthy": bool(response_time),
                    "details": "Redis доступен" if response_time else "Redis недоступен"}
        except Exception as e:
            return {"healthy": False, "details": str(e)}

    async def initialize_redis(self):
        """
        Инициализирует соединение с Redis.
        """
        try:
            self.redis_client = await redis.from_url(Config.REDIS_URL)
        except Exception as e:
            app_logger.error(f"Ошибка при инициализации Redis клиента: {e}")

    def check_firebase(self):
        return self.check_network_component(self.firebase_host, "Firebase")

    def check_telegram(self):
        return self.check_network_component(self.telegram_host, "Telegram")

    def check_gateway(self):
        return self.check_network_component(self.gateway_ip, "Шлюз")

    async def check_network_component(self, host: str, name: str) -> dict:
        """
        Общая логика проверки сетевых компонентов.
        """
        try:
            response_time = await self.ping_host(host)
            return {"healthy": bool(response_time),
                    "details": f"{name} доступен" if response_time else f"{name} недоступен", "infrm": response_time}
        except Exception as e:
            return {"healthy": False, "details": str(e)}

    async def ping_host(self, host: str) -> Union[float, None]:
        """
        Выполняет пинг указанного хоста.
        """
        try:
            return await asyncio.to_thread(ping, host, timeout=3)
        except PingError as e:
            app_logger.error(f"Ошибка пинга хоста {host}: {e}")
            return None

    def check_disk_space(self) -> dict:
        """
        Проверяет наличие свободного места на диске.
        """
        try:
            _, _, free = shutil.disk_usage("/")
            free_gb = free / (1024 ** 3)
            return {
                "healthy": free_gb >= Config.DISK_SPACE_THRESHOLD_GB,
                "details": f"Свободно: {free_gb:.2f} ГБ",
                "inform": f"{free_gb:.2f} ГБ"
            }
        except Exception as e:
            return {"healthy": False, "details": str(e)}

    def check_ram(self) -> dict:
        """
        Проверяет использование RAM.
        """
        try:
            mem = psutil.virtual_memory()
            available_gb = mem.available / (1024 ** 3)
            used_percent = mem.percent
            return {
                "healthy": used_percent <= Config.RAM_USAGE_THRESHOLD_PERCENT,
                "details": f"RAM используется на {used_percent}%",
                "inform": f"{available_gb:.2f} ГБ"
            }
        except Exception as e:
            return {"healthy": False, "details": str(e)}

    def get_task_status(self, task: asyncio.Task, task_name: str) -> dict:
        """
        Возвращает текущий статус указанной задачи.

        :param task: asyncio.Task - Задача, статус которой нужно проверить.
        :param task_name: str - Название задачи для идентификации.
        :return: dict - Словарь с состоянием задачи.
        """
        if not task:
            return {"task": task_name, "status": "NOT_STARTED", "details": "Задача еще не создана."}

        if task.done():
            return {"task": task_name, "status": "COMPLETED", "details": "Задача завершена."}

        if task.cancelled():
            return {"task": task_name, "status": "CANCELLED", "details": "Задача была отменена."}

        return {"task": task_name, "status": "RUNNING", "details": "Задача в процессе выполнения."}

    async def check_internet(self) -> dict:
        """
        Проверяет доступность интернета.
        """
        for host in self.hosts:
            result = await self.check_network_component(host, "Интернет")
            if result["healthy"]:
                return result
        return {"healthy": False, "details": "Интернет недоступен"}

    def calculate_system_health(self) -> dict:
        """
        Рассчитывает общее здоровье системы.
        """
        overall_status = "OK"
        failed, errors = [], []

        for name, status in self.statuses.items():
            if status["status"] == "FAILED":
                overall_status = "FAILED"
                failed.append(name)
            elif status["status"] == "ERROR":
                overall_status = "ERROR"
                errors.append(name)

        return {
            "system_status": overall_status,
            "failed_components": failed,
            "error_components": errors,
            "details": self.statuses,
        }

    async def generate_report(self) -> dict:

        """
        Формирует подробный отчет о состоянии всех компонентов в формате JSON.
        """
        try:
            # Выполняем детализированную проверку компонентов
            await self.perform_health_checks()

            # Генерация отчета
            report = {
                "components": {
                    name: {
                        "status": status.get("status", "N/A"),
                        "details": status.get("details", "No details available"),
                        "inform": status.get("inform", False),
                        "last_checked": status.get("last_checked", "N/A")
                    }
                    for name, status in self.statuses.items()
                }
            }

            return report
        except Exception as e:
            app_logger.error(f"Ошибка генерации отчета: {e}")
            raise ValueError(f"Ошибка генерации отчета: {e}")

    async def get_all_statuses(self) -> dict:
        """
        Возвращает текущий статус всех компонентов.
        """
        try:
            # Выполняем детализированную проверку состояния всех компонентов
            await self.perform_health_checks()

            # Формируем словарь статусов всех компонентов
            return {
                name: {
                    "title": self.titles.get(name, name),
                    "tooltip": self.component_tooltips.get(name, "Описание отсутствует"),
                    "status": status.get("status", "N/A"),
                    "details": status.get("details", "No details available"),
                    "inform": status.get("inform", "N/A"),
                    "last_checked": status.get("last_checked", "N/A"),
                }
                for name, status in self.statuses.items()
            }
        except Exception as e:
            app_logger.error(f"Ошибка получения статусов: {e}")
            raise ValueError(f"Ошибка получения статусов: {e}")
