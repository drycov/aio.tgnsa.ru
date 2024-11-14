import hashlib
from datetime import datetime
from random import randint
from typing import Optional, List, Union

from firebase_admin import db, exceptions
from pydantic import BaseModel, ValidationError

from app.utils.logger_instance import app_logger


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
        Создает нового пользователя в базе данных.
        """
        try:
            # Проверяем наличие обязательных полей
            required_fields = ['tg_id', 'first_name', 'last_name', 'email']

            missing_fields = [field for field in required_fields if field not in user_data or user_data[field] is None]
            if missing_fields:
                raise ValueError(
                    f"Отсутствуют обязательные поля для создания пользователя: {', '.join(missing_fields)}")

            # Создаем экземпляр пользователя
            user = cls(**user_data)

            # Запись в базу данных Firebase
            user_ref = db.reference(f'users/{user.tg_id}')
            user_ref.set(user.model_dump())

            # Логирование успешного создания пользователя
            app_logger.info(f"User {user.tg_id} created successfully.")
            return user

        except ValidationError as e:
            app_logger.error(f"Ошибка валидации при создании пользователя: {e}")
            raise
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

            # Логирование, если данные отсутствуют или формат неверен
            if not isinstance(user_snapshot, dict):
                app_logger.warning(f"Пользователь с tg_id {tg_id} не найден или данные не в ожидаемом формате.")
                return None

            # Проверка на обязательные поля
            missing_fields = [field for field in ["tg_id", "first_name", "last_name"] if field not in user_snapshot]
            if missing_fields:
                app_logger.warning(f"Отсутствуют обязательные поля для tg_id {tg_id}: {missing_fields}")
                return None

            # Валидация модели
            return cls.model_validate(user_snapshot)

        except ValidationError as e:
            app_logger.error(f"Ошибка валидации при создании пользователя с tg_id {tg_id}: {e}")
            return None
        except exceptions.FirebaseError as firebase_error:
            app_logger.error(f"Ошибка Firebase: {firebase_error}")
            return None
        except ValueError as value_error:
            # Обработка ошибок формата токена или его валидации
            app_logger.error(f"Ошибка валидации JWT токена: {value_error}")
            return None
        except Exception as error:
            app_logger.error(f"Ошибка при получении пользователя с tg_id {tg_id}: {error}")
            raise

    @classmethod
    def get_all(cls) -> List["User"]:
        """
        Получает список всех пользователей.
        """
        try:
            users_ref = db.reference('users')
            users_snapshot = users_ref.get()
            if not users_snapshot:
                app_logger.info("No users found.")
                return []
            return [cls(**user_data) for user_data in users_snapshot.values()] if isinstance(users_snapshot,
                                                                                             dict) else []
        except Exception as error:
            app_logger.error(f"Error fetching all users: {error}")
            raise

    def update(self, updates: dict) -> Optional["User"]:
        """
        Обновляет данные пользователя.
        """
        try:
            user_ref = db.reference(f'users/{self.tg_id}')

            # Выполнение обновления данных
            user_ref.update(updates)

            # Получение обновленных данных пользователя
            updated_user = user_ref.get()

            if not isinstance(updated_user, dict):
                app_logger.warning(f"User with tg_id {self.tg_id} not found or data is not in expected format.")
                return None

            app_logger.info(f"User {self.tg_id} updated successfully.")
            return User(**updated_user)

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
            admins_snapshot = users_ref.order_by_child('is_admin').equal_to(True).get()
            if not admins_snapshot:
                app_logger.info("No admin users found.")
                return []
            return [cls(**admin_data) for admin_data in admins_snapshot.values()] if isinstance(admins_snapshot,
                                                                                                dict) else []
        except Exception as error:
            app_logger.error(f"Error fetching admin users: {error}")
            raise

    class Config:
        json_schema_extra = {
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
