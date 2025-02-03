import uvicorn
import argparse
from api import API
from bot.utils import MACVendorLookup
from bot.utils.logger_instance import app_logger


# Экспорт приложения для использования с Uvicorn
def create_app():
    """
    Создание приложения FastAPI с жизненным циклом.
    """
    api = API()
    app = api.get_app()  # Lifespan уже настроен в классе API
    mac_lookup = MACVendorLookup()

    # Optionally load saved data
    mac_lookup.load_from_file()
    # Update data if necessary
    if not mac_lookup.macs_to_companies:
        if mac_lookup.update_data():
            mac_lookup.save_to_file()
    return app


# Экспорт приложения
app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск FastAPI приложения")
    parser.add_argument("--reload", action="store_true", help="Включить режим автоматической перезагрузки")
    parser.add_argument("--workers", type=int, default=1, help="Количество рабочих процессов (по умолчанию: 1)")

    args = parser.parse_args()
    app_logger.info("Запуск FastAPI приложения")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=args.reload, workers=args.workers
)
