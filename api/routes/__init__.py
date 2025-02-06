from fastapi import FastAPI, APIRouter

from bot.utils.logger_instance import app_logger  # Подключение логирования


PingManager = APIRouter()

@PingManager.get("/ping", summary="Проверка доступности API", tags=["Ping"])
async def ping():
    """
    Проверка доступности API.
    """
    return {"status": "ok", "message": "API доступен"}


def register_routes(app: FastAPI) -> None:
    """
    Регистрация маршрутов API.
    """
    try:
        from .index import Index
        from .user_manager import UserManager
        from .config_manager import ConfigManager
        from .health_manager import HealthManager
        from .subscriber_manager import SubscriberManager
        # from .tasks_manager import TasksManager

        # Регистрация маршрутов
        app.include_router(Index, prefix="/api", tags=["Index"])
        app.include_router(UserManager, prefix="/api", tags=["User Management"])
        app.include_router(ConfigManager, prefix="/api", tags=["Config Management"])
        app.include_router(HealthManager, prefix="/api", tags=["Health Monitoring"])
        app.include_router(PingManager, prefix="/api", tags=["Ping"])  # Добавлено
        app.include_router(SubscriberManager, prefix="/api", tags=["Subscriber"])
        # app.include_router(TasksManager, prefix="/tasks", tags=["Task Management"])

        app_logger.info("Маршруты успешно зарегистрированы.")
    except ImportError as e:
        app_logger.error(f"Ошибка при импорте маршрутов: {e}")
        raise
    except Exception as e:
        app_logger.error(f"Ошибка при регистрации маршрутов: {e}")
        raise
