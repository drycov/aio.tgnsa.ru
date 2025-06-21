import signal
import sys
import time

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import logger, settings
from app.plugins.manager import PluginManager


def example_task():
    logger.info("🧪 Выполняется example_task — демонстрационная задача.")


def job_listener(event):
    job_id = getattr(event, "job_id", "unknown")
    if event.exception:
        logger.error(f"❌ Ошибка при выполнении задачи: {job_id}")
    else:
        logger.debug(f"✅ Задача {job_id} выполнена успешно.")


def setup_plugins(scheduler: BackgroundScheduler):
    manager = PluginManager.create_once()

    manager.load_all()
    manager.init_all(settings)
    manager.register_scheduler(scheduler)


def run_scheduler():
    logger.info("🕒 Инициализация планировщика задач...")

    scheduler = BackgroundScheduler(timezone="UTC")

    # Зарегистрировать демонстрационную задачу
    scheduler.add_job(
        func=example_task,
        trigger=IntervalTrigger(seconds=60),
        id="example_task",
        name="Проверка example_task",
        replace_existing=True,
    )

    # Подключение всех плагинов
    setup_plugins(scheduler)

    # Подключение слушателей событий
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.start()

    logger.info("📅 Планировщик запущен. Используйте Ctrl+C для остановки.")

    # Блокирующий режим
    try:
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Инициирована остановка планировщика...")
        scheduler.shutdown(wait=True)
        logger.info("✔️ Планировщик остановлен.")
        sys.exit(0)

    # Не блокирующий режим
    scheduler.shutdown(wait=False)
    logger.info("✔️ Планировщик остановлен.")
