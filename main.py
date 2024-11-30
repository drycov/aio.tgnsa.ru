import uvicorn

from api import API
from bot.utils.logger_instance import app_logger


# Экспорт приложения для использования с Uvicorn
def create_app():
    """
    Создание приложения FastAPI с жизненным циклом.
    """
    api = API()
    app = api.get_app()  # Lifespan уже настроен в классе API
    return app


# Экспорт приложения
app = create_app()

if __name__ == "__main__":
    app_logger.info("Запуск FastAPI приложения")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
