import hashlib
from datetime import datetime, timedelta, timezone
from random import randint
from typing import Optional, List, Union

import jwt
from firebase_admin import db, exceptions
from pydantic import BaseModel, ValidationError, ConfigDict

from app.utils.logger_instance import app_logger
from config import Config


class User(BaseModel):
    is_bot: bool = False
    tg_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_post: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    is_admin: Optional[bool] = False
    is_allowed: Optional[bool] = False
    is_verified: Optional[bool] = False
    verification_code: Optional[Union[int, str]] = None
    email: Optional[str] = None
    hash: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_bot": False,
                "ttc_id": "123456",
                "station": "Central",
                "tg_id": 123456789,
                "first_name": "John",
                "last_name": "Doe",
                "company_post": "Engineer",
                "phone_number": "+1234567890",
                "username": "johndoe",
                "is_admin": True,
                "user_allowed": True,
                "verification_code": "ABC123",
                "email": "johndoe@example.com",
                "user_verified": True,
                "api_token": "token_123456",
                "hash": "hash_value"
            }
        }
    )

    @classmethod
    def from_firebase(cls, data: dict) -> "User":
        from app.utils.helper_functions import HelperFunctions  # Импорт внутри метода
        """
        Создает объект User из данных Firebase с безопасным декодированием строк.
        """
        return cls(
            tg_id=data.get("tg_id", 0),
            first_name=HelperFunctions.safe_decode(data.get("first_name")),
            last_name=HelperFunctions.safe_decode(data.get("last_name")),
            company_post=HelperFunctions.safe_decode(data.get("company_post")),
            phone_number=HelperFunctions.safe_decode(data.get("phone_number")),
            username=HelperFunctions.safe_decode(data.get("username")),
            is_admin=data.get("is_admin", False),
            is_allowed=data.get("is_allowed", False),
            is_verified=data.get("is_verified", False),
            verification_code=data.get("verification_code"),
            email=HelperFunctions.safe_decode(data.get("email")),
            hash=data.get("hash")
        )

    @staticmethod
    def generate_verification_code() -> str:
        """
        Генерирует 6-значный числовой код для верификации.
        """
        return str(randint(100000, 999999))

    @staticmethod
    def generate_hash(email: str) -> str:
        """
        Генерирует хэш на основе email пользователя и текущего времени.
        """
        return hashlib.sha256(f"{email}{datetime.now()}".encode()).hexdigest()

    def verify_code(self, code: str) -> bool:
        """
        Проверяет, совпадает ли введённый код с верификационным кодом пользователя.
        """
        return self.verification_code == code

        # Метод для проверки, является ли пользователь администратором

    def is_admin_user(self) -> bool:
        """
        Проверяет, является ли пользователь администратором.
        """
        return self.is_admin

    def is_allowed_user(self) -> bool:
        """
        Проверяет, является ли пользователь администратором.
        """
        return self.is_allowed

    def is_verified_user(self) -> bool:
        """
        Проверяет, является ли пользователь администратором.
        """
        return self.is_verified

    @classmethod
    def create(cls, user_data: dict) -> "User":
        """
        Создает нового пользователя в базе данных с безопасным декодированием строк.
        """
        try:
            required_fields = ["tg_id", "first_name", "last_name", "email"]
            missing_fields = [field for field in required_fields if not user_data.get(field)]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Создание пользователя с безопасным декодированием
            user = cls.from_firebase(user_data)

            # Запись в базу данных Firebase
            user_ref = db.reference(f'users/{user.tg_id}')
            user_ref.set(user.model_dump())

            app_logger.info(f"User {user.tg_id} created successfully.")
            return user
        except Exception as error:
            app_logger.error(f"Error creating user: {error}")
            raise

    @classmethod
    def get_by_tg_id(cls, tg_id: int) -> Optional["User"]:
        """
        Получает пользователя по tg_id.
        """
        try:
            user_ref = db.reference(f'users/{tg_id}')
            user_snapshot = user_ref.get()

            # Проверка наличия данных и их формата
            if not isinstance(user_snapshot, dict):
                app_logger.warning(
                    f"Пользователь с tg_id {tg_id} не найден или данные не в ожидаемом формате: {type(user_snapshot)}")
                return None

            # Создание объекта User через метод from_firebase
            user = cls.from_firebase(user_snapshot)
            app_logger.info(f"Пользователь с tg_id {tg_id} успешно получен.")
            return user

        except ValidationError as e:
            app_logger.error(f"Ошибка валидации при создании пользователя с tg_id {tg_id}: {e}")
            return None
        except exceptions.FirebaseError as firebase_error:
            app_logger.error(f"Ошибка Firebase: {firebase_error}")
            return None
        except Exception as error:
            app_logger.error(f"Ошибка при получении пользователя с tg_id {tg_id}: {error}")
            raise

    @classmethod
    def get_all(cls) -> List["User"]:
        """
        Получает список всех пользователей с безопасным декодированием строк.
        """
        try:
            users_ref = db.reference("users")
            users_snapshot = users_ref.get()

            # Проверка на отсутствие данных
            if not users_snapshot:
                app_logger.info("No users found.")
                return []

            # Проверка типа данных
            if not isinstance(users_snapshot, dict):
                app_logger.warning(f"Unexpected format for users_snapshot: {type(users_snapshot)}")
                return []

            # Обработка данных
            return [
                cls.from_firebase(user_data)
                for user_data in users_snapshot.values()
                if isinstance(user_data, dict)
            ]
        except Exception as error:
            app_logger.error(f"Error fetching all users: {error}")
            raise

    def update(self, updates: dict) -> Optional["User"]:
        from app.utils.helper_functions import HelperFunctions  # Импорт внутри метода

        """
        Обновляет данные пользователя с безопасным декодированием строк.
        """
        try:
            user_ref = db.reference(f'users/{self.tg_id}')

            # Декодируем строки в словаре updates
            updates = {
                key: HelperFunctions.safe_decode(value) if isinstance(value, str) else value
                for key, value in updates.items()
            }

            # Обновляем данные в Firebase
            user_ref.update(updates)

            # Получаем обновленные данные
            updated_user = user_ref.get()

            # Проверка типа данных
            if not isinstance(updated_user, dict):
                app_logger.warning(f"Unexpected format for updated_user: {type(updated_user)}")
                return None

            return User.from_firebase(updated_user)
        except Exception as error:
            app_logger.error(f"Error updating user {self.tg_id}: {error}")
            raise

    @classmethod
    def delete(cls, tg_id: int) -> None:
        """
        Удаляет пользователя по tg_id.
        """
        try:
            user_ref = db.reference(f'users/{tg_id}')
            user_ref.delete()
            app_logger.info(f"User {tg_id} deleted successfully.")
        except Exception as error:
            app_logger.error(f"Error deleting user {tg_id}: {error}")
            raise

    @classmethod
    def get_admin_users(cls) -> List["User"]:
        """
        Получает список всех администраторов.
        """
        try:
            users_ref = db.reference('users')

            # Получение только администраторов
            admins_snapshot = users_ref.order_by_child('is_admin').equal_to(True).get()

            # Если администраторов нет
            if not admins_snapshot:
                app_logger.info("No admin users found.")
                return []

            # Проверка формата и создание объектов User через from_firebase
            if not isinstance(admins_snapshot, dict):
                app_logger.warning(f"Unexpected format for admins_snapshot: {type(admins_snapshot)}")
                return []

            return [
                cls.from_firebase(admin_data)
                for admin_data in admins_snapshot.values()
                if isinstance(admin_data, dict)
            ]

        except Exception as error:
            app_logger.error(f"Error fetching admin users: {error}")
            raise

    @staticmethod
    def generate_jwt(user_id: int, secret_key: str = Config.SECRET_KEY, expires_in: int = 60) -> str:
        """
        Генерирует JWT токен с информацией о пользователе.
        :param user_id: Идентификатор пользователя (tg_id).
        :param secret_key: Секретный ключ для подписи токена.
        :param expires_in: Время жизни токена в минутах (по умолчанию 60 минут).
        :return: Строка JWT токенsа.
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_in),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')

    @staticmethod
    def decode_jwt(token: str, secret_key: str) -> Optional[dict]:
        """
        Декодирует JWT токен и возвращает данные пользователя, если токен валиден.
        :param token: JWT токен.
        :param secret_key: Секретный ключ для проверки подписи токена.
        :return: Словарь с данными пользователя или None, если токен недействителен.
        """
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            app_logger.warning("JWT токен просрочен.")
            return None
        except jwt.InvalidTokenError:
            app_logger.error("Неверный JWT токен.")
            return None
