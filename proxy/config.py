import logging
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent

# Директория для хранения SSL-сертификатов
cert_dir = BASE_DIR / "certs"
cert_dir.mkdir(parents=True, exist_ok=True)

# Пути к файлам сертификатов
CERT_FILE = cert_dir / "server.crt"
KEY_FILE = cert_dir / "server.key"

datadir = BASE_DIR / "data"
datadir.mkdir(parents=True, exist_ok=True)

# Путь к базе данных пользователей
DB_FILE = datadir / "users.db"

# Параметры сервера
SERVER_IP = "0.0.0.0"  # Адрес, на котором сервер будет прослушивать подключения
SERVER_PORT = 5000  # Порт сервера
logdir = BASE_DIR / "log"
logdir.mkdir(parents=True, exist_ok=True)
REMOTE_SERVER_IP = "127.0.0.1"
REMOTE_SERVER_PORT = 8000

# Настройка логирования
LOG_FILE = logdir / "vpn.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,  # Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",  # Добавляем поддержку UTF-8

)
logger = logging.getLogger(__name__)
