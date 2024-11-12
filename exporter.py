import sys
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, db
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from tqdm import tqdm

from app.models import User
from app.utils.logger_instance import app_logger
from config import Config

# Конфигурация MongoDB
uri = "mongodb+srv://ttc-ttcnsa:3Gm69K7l5R6v0CNT@cluster0.c48ewsz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))

# Проверка подключения к MongoDB
try:
    client.admin.command('ping')
    app_logger.info("Успешное подключение к MongoDB!")
except Exception as e:
    app_logger.error(f"Ошибка подключения к MongoDB: {e}")
    sys.exit(1)

mongo_db = client["isl"]
mongo_collection = mongo_db["users"]

# Инициализация Firebase
try:
    if not firebase_admin._apps:
        serviceAccountKey = Path(Config.BASE_DIR) / "serviceAccountKey.json"
        app_logger.info(f"Инициализация Firebase с файлом ключа: {serviceAccountKey}")
        cred = credentials.Certificate(serviceAccountKey)
        firebase_admin.initialize_app(cred, {
            'databaseURL': Config.FIREBASE_DATABASE_URL
        })
        app_logger.info("Firebase успешно инициализирован")
except Exception as e:
    app_logger.error(f"Ошибка при инициализации Firebase: {e}")
    sys.exit(1)


# Функция для экспорта данных из MongoDB в Firebase с использованием модели User
# Функция для экспорта данных из MongoDB в Firebase с использованием модели User
def export_to_firebase():
    # Получение всех данных из коллекции MongoDB
    documents = list(mongo_collection.find())
    total_docs = len(documents)

    for doc in tqdm(documents, total=total_docs, desc="Экспорт данных", unit="запись"):
        try:
            # Проверяем наличие и корректность поля id
            tg_id = doc.get("_id")
            if tg_id is None:
                app_logger.warning(f"Пропущен пользователь из-за отсутствия 'id': {doc}")
                continue  # Пропускаем запись без tg_id

            # Преобразование данных в модель User
            user_data = {
                "tg_id": int(tg_id),  # Преобразуем tg_id только если он не None
                "first_name": doc.get("firstName"),
                "last_name": doc.get("lastName"),
                "company_post": doc.get("companyPost"),
                "phone_number": doc.get("phoneNumber"),
                "username": doc.get("username"),
                "is_admin": doc.get("isAdmin", False),
                "is_allowed": doc.get("isAllowed", False),
                "is_verified": doc.get("isVerified", False),
                "verification_code": doc.get("verificationCode"),
                "email": doc.get("email"),
                "hash": doc.get("hash"),
            }

            # Валидация и создание пользователя через модель User
            user = User(**user_data)

            # Сохранение пользователя в Firebase
            user_ref = db.reference(f'users/{user.tg_id}')
            user_ref.set(user.dict())

            app_logger.info(f"Экспортирован пользователь: {user.first_name} {user.last_name}")

        except Exception as e:
            app_logger.error(f"Ошибка при экспорте пользователя {doc.get('id')}: {e}")

    app_logger.info("Экспорт завершен")


# Основной запуск скрипта
if __name__ == "__main__":
    app_logger.info("Запуск экспорта данных из MongoDB в Firebase")
    export_to_firebase()
    app_logger.info("Процесс экспорта завершен")
