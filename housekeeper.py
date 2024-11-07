import asyncio
import os
import time

from app.bot_instance import redis_client
from app.utils.logger_instance import app_logger
from config import Config
from logging_config import LoggingConfig


class Housekeeper:
    def __init__(self):
        """
        Инициализирует параметры для housekeeper, используя настройки из Config.
        """
        self.enabled = Config.HOUSEKEEPER_ENABLED
        self.logs_dir = LoggingConfig.LOG_DIR
        self.days_threshold = Config.HOUSEKEEPER_DAYS_THRESHOLD
        self.inactivity_threshold = Config.HOUSEKEEPER_INACTIVITY_THRESHOLD
        self.interval = Config.HOUSEKEEPER_INTERVAL
        self.max_threads = Config.HOUSEKEEPER_MAX_THREADS
        self.max_requests = Config.HOUSEKEEPER_MAX_REQUESTS
        self.max_concurrent_requests = Config.HOUSEKEEPER_MAX_CONCURRENT_REQUESTS
        self.max_retry_attempts = Config.HOUSEKEEPER_MAX_RETRY_ATTEMPTS
        self.max_retry_delay = Config.HOUSEKEEPER_MAX_RETRY_DELAY
        self.retry_delay_multiplier = Config.HOUSEKEEPER_RETRY_DELAY_MULTIPLIER
        self.max_queue_size = Config.HOUSEKEEPER_MAX_QUEUE_SIZE
        self.queue_name = Config.HOUSEKEEPER_QUEUE_NAME
        self.task_name = Config.HOUSEKEEPER_TASK_NAME
        self.task_class = Config.HOUSEKEEPER_TASK_CLASS

        # Проверка на контейнерное окружение и корректировка логов
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
        Основной цикл housekeeper, который периодически запускает задачи очистки.
        """
        if not self.enabled:
            app_logger.info("Housekeeper отключён, запуск пропущен.")
            return

        app_logger.info("Запуск Housekeeper...")

        while True:
            try:
                await self.cleanup_inactive_users()
                self.cleanup_logs()
            except Exception as e:
                app_logger.error(f"Ошибка в Housekeeper: {e}")
            # Ожидание перед следующим циклом очистки
            await asyncio.sleep(self.interval)

    async def cleanup_inactive_users(self):
        """
        Очищает данные неактивных пользователей из Redis, если они неактивны дольше порога.
        """
        try:
            current_time = int(time.time())
            keys_pattern = "fsm:*:last_activity"
            keys = await redis_client.keys(keys_pattern)

            for key in keys:
                last_activity = await redis_client.get(key)
                if last_activity:
                    last_activity = int(last_activity)
                    inactivity_period = current_time - last_activity

                    if inactivity_period > self.inactivity_threshold:
                        # Удаляем данные пользователя
                        user_id = key.decode().split(":")[1]
                        await redis_client.delete(key)
                        await redis_client.delete(f"fsm:{user_id}:state")
                        await redis_client.delete(f"fsm:{user_id}:data")

                        app_logger.info(
                            f"Удалены данные неактивного пользователя {user_id} после {inactivity_period} секунд неактивности.")
        except Exception as e:
            app_logger.error(f"Ошибка при очистке неактивных пользователей: {e}")

    def cleanup_logs(self):
        """
        Удаляет файлы в указанной директории, которые были изменены более чем `days_threshold` дней назад.
        """
        try:
            now = time.time()
            cutoff_time = now - self.days_threshold * 86400  # 86400 секунд в дне

            # Проверка существования директории логов перед очисткой
            if not os.path.exists(self.logs_dir):
                app_logger.warning(f"Директория логов {self.logs_dir} не существует. Пропуск очистки логов.")
                return

            for filename in os.listdir(self.logs_dir):
                file_path = os.path.join(self.logs_dir, filename)

                if os.path.isfile(file_path):
                    file_mod_time = os.path.getmtime(file_path)
                    if file_mod_time < cutoff_time:
                        try:
                            os.remove(file_path)
                            app_logger.info(f"Удален старый лог-файл: {file_path}")
                        except Exception as e:
                            app_logger.error(f"Ошибка при удалении файла {file_path}: {e}")
        except Exception as e:
            app_logger.error(f"Ошибка при очистке логов: {e}")

    async def report_status(self):
        """
        Отчётный метод, который можно вызвать для логирования текущего статуса очистки и активности.
        """
        app_logger.info("Housekeeper Status Report")
        app_logger.info(f"Проверка директории логов: {self.logs_dir}")
        app_logger.info(f"Логи старше {self.days_threshold} дней будут удалены.")
        app_logger.info(f"Порог неактивности пользователей: {self.inactivity_threshold} секунд.")
        app_logger.info(f"Интервал запуска задач: каждые {self.interval} секунд.")
        app_logger.info(f"Максимальное количество потоков: {self.max_threads}")
        app_logger.info(f"Максимальное количество запросов: {self.max_requests}")
        app_logger.info(f"Максимальное количество параллельных запросов: {self.max_concurrent_requests}")
        app_logger.info(f"Максимальное количество попыток повторного выполнения: {self.max_retry_attempts}")
        app_logger.info(f"Задержка перед повторной попыткой: {self.max_retry_delay} секунд")
        app_logger.info(f"Множитель задержки перед повторной попыткой: {self.retry_delay_multiplier}")
        app_logger.info(f"Имя очереди: {self.queue_name}")
        app_logger.info(f"Имя задачи: {self.task_name}")
        app_logger.info(f"Класс задачи: {self.task_class}")
