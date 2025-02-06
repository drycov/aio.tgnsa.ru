import uvicorn
import argparse
from api import API
from bot.utils import MACVendorLookup
from bot.utils.logger_instance import app_logger
import os
import sys


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


# Функция для записи PID в файл
def write_pid(pid_file="pid.run"):
    """
    Записывает PID процесса в файл при старте приложения.
    """
    try:
        pid = os.getpid()
        if os.path.exists(pid_file):
            app_logger.warning(f"Warning: {pid_file} already exists. Process might already be running.")
        with open(pid_file, "w") as f:
            f.write(str(pid))  # Записываем PID в файл
        app_logger.info(f"Process PID {pid} written to {pid_file}")
    except Exception as e:
        app_logger.error(f"Error creating PID file: {e}")
        sys.exit(1)  # Завершаем приложение в случае ошибки


# Функция для удаления файла PID при завершении
def remove_pid(pid_file="pid.run"):
    """
    Удаляет файл PID при завершении работы приложения.
    """
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
            app_logger.info(f"{pid_file} removed.")
    except Exception as e:
        app_logger.error(f"Error removing PID file: {e}")


# Экспорт приложения
app = create_app()

if __name__ == "__main__":
    # Записываем PID в файл при старте
    write_pid()
    parser = argparse.ArgumentParser(description="Запуск FastAPI приложения")
    parser.add_argument("--reload", action="store_true", help="Включить режим автоматической перезагрузки")
    parser.add_argument("--workers", type=int, default=1, help="Количество рабочих процессов (по умолчанию: 1)")

    args = parser.parse_args()
    app_logger.info("Запуск FastAPI приложения")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=args.reload, workers=args.workers)
    # Удаляем файл PID при завершении работы
    remove_pid()
