import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.triggers.interval import IntervalTrigger
from app.core.applcm_manager import AppLifecycleManager
from app.core.config import logger, settings
from app.core.plugin_manager import PluginManager


class SchedulerManager:
    def __init__(self, lifecycle_manager: AppLifecycleManager):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.lifecycle_manager = lifecycle_manager

        # Регистрация lifecycle hooks

        lifecycle_manager.on_startup(name="scheduler_startup")(self.start)
        lifecycle_manager.on_shutdown(name="scheduler_shutdown")(self.shutdown)
        self.setup_plugins()
        self.scheduler.add_listener(
            self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

    def example_task(self):
        logger.info("🧪 Выполняется example_task — демонстрационная задача.")

    def job_listener(self, event):
        job_id = getattr(event, "job_id", "unknown")
        if event.exception:
            logger.error(f"❌ Ошибка при выполнении задачи: {job_id}")
        else:
            logger.debug(f"✅ Задача {job_id} выполнена успешно.")

    def setup_plugins(self):
        manager = PluginManager.create_once()
        manager.ensure_initialized(settings)
        manager.register_scheduler(self.scheduler)

    async def start(self):
        logger.info("🕒 Запуск планировщика задач...")
        self.scheduler.start()
        logger.info("📅 Планировщик запущен.")

    async def shutdown(self):
        logger.info("🛑 Остановка планировщика задач...")
        self.scheduler.shutdown(wait=True)
        logger.info("✔️ Планировщик остановлен.")


def run_scheduler(lifecycle: AppLifecycleManager):
    task_manager = SchedulerManager(lifecycle)

    import asyncio

    async def main():
        await lifecycle.startup()

        # Блокируем выполнение до получения сигнала (например, через asyncio.Event)
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Сигнал завершения получен, запускаем завершение...")

        await lifecycle.shutdown()

    asyncio.run(main())
