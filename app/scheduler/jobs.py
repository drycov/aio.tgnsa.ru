import signal
import sys
import time

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import logger


def example_task():
    logger.info("✅ Выполняется плановая задача: example_task")
    # Здесь может быть ваша логика (запросы, проверка состояний, и т.д.)
    # raise Exception("Test fail")  # Пример для логирования ошибки


def job_listener(event):
    if event.exception:
        logger.error(f"❌ Ошибка при выполнении задачи: {event.job_id}")
    else:
        logger.debug(f"✅ Задача {event.job_id} выполнена успешно.")


def run_scheduler():
    logger.info("🕒 Планировщик инициализирован.")

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        func=example_task,
        trigger=IntervalTrigger(seconds=60),
        id="example_task",
        name="Периодическая проверка состояния",
        replace_existing=True,
    )

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.start()

    logger.info("📅 Планировщик запущен. Нажмите Ctrl+C для остановки.")

    try:
        # Блокирующий цикл для работы в CLI-режиме
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Остановка планировщика...")
        scheduler.shutdown()
        logger.info("✔️ Планировщик завершил работу.")
        sys.exit(0)
