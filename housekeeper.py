import os
import time
from typing import List, Optional, Dict

import redis.asyncio as redis  # Используем асинхронный Redis клиент
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.utils.logger_instance import app_logger
from config import Config
from logging_config import LoggingConfig


class Housekeeper:
    scheduler: AsyncIOScheduler

    def __init__(self, scheduler: AsyncIOScheduler):
        """
        Инициализирует параметры для housekeeper, используя настройки из Config.
        """
        self.scheduler = scheduler
        self.enabled = Config.HOUSEKEEPER_ENABLED
        self.logs_dir = LoggingConfig.LOG_DIR
        self.days_threshold = Config.HOUSEKEEPER_DAYS_THRESHOLD
        self.inactivity_threshold = Config.HOUSEKEEPER_INACTIVITY_THRESHOLD
        self.redis_client = None

        # Логирование
        if Config.IS_CONTAINER:
            app_logger.info("Housekeeper запущен в контейнере с уменьшенным количеством ресурсов.")
        else:
            app_logger.info("Housekeeper запущен на сервере с полной конфигурацией ресурсов.")

        # Проверка существования директории логов
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            app_logger.info(f"Создана директория для логов: {self.logs_dir}")

    async def run(self):
        """
        Основной метод запуска Housekeeper для запуска фоновых задач.
        """
        self.schedule_tasks()  # Запуск всех запланированных задач
        app_logger.info("Housekeeper задачи запланированы и запущены.")

    async def initialize_redis(self):
        """
        Инициализирует соединение с Redis.
        """
        try:
            self.redis_client = await redis.from_url(Config.REDIS_URL)
        except Exception as e:
            app_logger.error(f"Ошибка при инициализации Redis клиента: {e}")
            raise

    def schedule_tasks(self):
        """
        Запускает задачи через APScheduler.
        """
        if not self.enabled:
            app_logger.info("Housekeeper отключён, задачи не запланированы.")
            return

        # Планируем задачи
        self.scheduler.add_job(self.cleanup_inactive_users, IntervalTrigger(seconds=Config.HOUSEKEEPER_INTERVAL))
        self.scheduler.add_job(self.cleanup_logs, CronTrigger(hour=3))  # Запуск каждый день в 3 утра
        app_logger.info("Housekeeper задачи запланированы.")

    async def cleanup_inactive_users(self):
        """
        Очищает данные неактивных пользователей из Redis.
        """
        try:
            if not self.redis_client:
                await self.initialize_redis()
            current_time = int(time.time())
            keys_pattern = "fsm:*:last_activity"
            keys = await self.redis_client.keys(keys_pattern)
            for key in keys:
                last_activity = await self.redis_client.get(key)
                if last_activity:
                    last_activity = int(last_activity)
                    inactivity_period = current_time - last_activity

                    if inactivity_period > self.inactivity_threshold:
                        user_id = key.decode().split(":")[1]
                        await self.redis_client.delete(key)
                        await self.redis_client.delete(f"fsm:{user_id}:state")
                        await self.redis_client.delete(f"fsm:{user_id}:data")
                        app_logger.info(
                            f"Удалены данные неактивного пользователя {user_id} после {inactivity_period} секунд.")
        except Exception as e:
            app_logger.error(f"Ошибка при очистке неактивных пользователей: {e}")

    def cleanup_logs(self):
        """
        Удаляет старые логи.
        """
        try:
            now = time.time()
            cutoff_time = now - self.days_threshold * 86400

            if not os.path.exists(self.logs_dir):
                app_logger.warning(f"Директория логов {self.logs_dir} не существует. Пропуск очистки.")
                return

            for filename in os.listdir(self.logs_dir):
                file_path = os.path.join(self.logs_dir, filename)
                if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    app_logger.info(f"Удален старый лог-файл: {file_path}")
        except Exception as e:
            app_logger.error(f"Ошибка при очистке логов: {e}")

    def get_all_jobs(self) -> List[Dict[str, Optional[str]]]:
        """
        Получает список всех задач из AsyncIOScheduler.
        """
        try:
            jobs = self.scheduler.get_jobs()
            job_list = []

            for job in jobs:
                job_list.append({
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger),
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
                })

            return job_list
        except Exception as e:
            app_logger.error(f"Error fetching all jobs: {e}")
            raise

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Optional[str]]]:
        """
        Получает информацию о задаче по её ID.
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                app_logger.warning(f"Job with ID {job_id} not found.")
                return None

            return {
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            }
        except Exception as e:
            app_logger.error(f"Error fetching job with ID {job_id}: {e}")
            raise
