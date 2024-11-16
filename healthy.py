import asyncio
import shutil

from firebase_admin import db

from app.bot_instance import storage
from app.utils.logger_instance import app_logger
from config import Config


class Healthy:
    def __init__(self):
        """
        Инициализирует класс Healthy с настройками из Config.
        """
        self.check_interval = Config.HEALTHY_CHECK_INTERVAL  # Проверка каждые 5 минут по умолчанию
        self.components = {
            "redis": self.check_redis,
            "firebase": self.check_firebase,
            "disk_space": self.check_disk_space
        }
        self.statuses = {}  # Для хранения статусов компонентов

    async def run(self):
        """
        Запускает циклическую проверку состояния компонентов.
        """
        while True:
            try:
                await self.perform_health_checks()
            except Exception as e:
                app_logger.error(f"Ошибка при выполнении проверки здоровья: {e}")
            await asyncio.sleep(self.check_interval)

    async def perform_health_checks(self):
        """
        Выполняет проверку здоровья всех зарегистрированных компонентов и логирует результаты.
        """
        for name, check_function in self.components.items():
            try:
                # Для асинхронных функций используем await, для синхронных — прямой вызов
                if asyncio.iscoroutinefunction(check_function):
                    is_healthy = await check_function()
                else:
                    is_healthy = check_function()

                status = "OK" if is_healthy else "FAILED"
                self.statuses[name] = status  # Сохранение статуса
                app_logger.info(f"Проверка компонента {name}: {status}")
            except Exception as e:
                self.statuses[name] = "ERROR"
                app_logger.error(f"Ошибка при проверке {name}: {e}")

    def register_component(self, name: str, check_function) -> None:
        """
        Регистрирует новый компонент для проверки.
        """
        self.components[name] = check_function
        app_logger.info(f"Зарегистрирован новый компонент: {name}")

    async def get_component_status(self, name: str) -> str:
        """
        Возвращает текущий статус указанного компонента.
        """
        if name in self.components:
            try:
                is_healthy = await self.components[name]()
                status = "OK" if is_healthy else "FAILED"
                self.statuses[name] = status
                return status
            except Exception as e:
                app_logger.error(f"Ошибка при проверке {name}: {e}")
                return "ERROR"
        else:
            app_logger.warning(f"Компонент {name} не зарегистрирован.")
            return "NOT_REGISTERED"

    async def get_all_statuses(self) -> dict:
        """
        Возвращает текущий статус всех компонентов.
        """
        await self.perform_health_checks()
        return self.statuses

    def generate_report(self) -> str:
        """
        Формирует отчет о состоянии всех компонентов.
        """
        report_lines = ["Состояние компонентов:"]
        for name, status in self.statuses.items():
            report_lines.append(f"{name}: {status}")
        return "\n".join(report_lines)

    async def check_redis(self) -> bool:
        """
        Проверяет доступность Redis.
        """
        try:
            await storage.ping()
            return True
        except Exception as e:
            app_logger.error(f"Redis не доступен: {e}")
            return False

    async def check_firebase(self) -> bool:
        """
        Проверяет доступность Firebase.
        """
        try:
            reference = db.reference('/')
            reference.get()
            return True
        except Exception as e:
            app_logger.error(f"Firebase не доступен: {e}")
            return False

    def check_disk_space(self) -> bool:
        """
        Проверяет наличие свободного места на диске.
        """
        try:
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024 ** 3)
            if free_gb < Config.DISK_SPACE_THRESHOLD_GB:
                app_logger.warning(f"Недостаточно места на диске: осталось {free_gb:.2f} ГБ")
                return False
            return True
        except Exception as e:
            app_logger.error(f"Ошибка при проверке дискового пространства: {e}")
            return False
