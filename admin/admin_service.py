"""
This module provides services for managing admin-related operations, such as fetching and updating users.
"""

from typing import Optional

from firebase_admin import db
from pydantic import ValidationError

from app.models import User
from app.utils.logger_instance import app_logger


class AdminService:
    """
    A service class for managing users and their roles in Firebase.
    """

    @staticmethod
    def get_all_users() -> list[User]:
        """
        Получает список всех пользователей из Firebase с обработкой ошибок.
        """
        try:
            users_ref = db.reference("users")
            users_snapshot = users_ref.get()
            if not users_snapshot:
                app_logger.info("No users found.")
                return []

            users = []
            for data in users_snapshot.values():
                if not isinstance(data, dict):
                    app_logger.warning("Invalid user data format: %s", data)
                    continue

                # Проверяем наличие обязательных полей
                if "tg_id" not in data:
                    app_logger.warning("Missing tg_id in user data: %s", data)
                    continue

                try:
                    user = User(**data)
                    users.append(user)
                except ValidationError as e:
                    app_logger.error("Validation error for user: %s - %s", data, e)
                    continue

            return users
        except Exception as e:
            app_logger.error("Error fetching all users: %s", e)
            raise

    @staticmethod
    def update_user_role(tg_id: int, is_admin: bool) -> Optional[User]:
        """
        Обновляет роль пользователя (is_admin) в базе данных Firebase.
        """
        try:
            # Обновляем данные пользователя в Firebase
            user_ref = db.reference(f'users/{tg_id}')
            user_ref.update({"is_admin": is_admin})

            # Получаем обновлённые данные
            updated_user = user_ref.get()

            # Проверяем, что данные существуют и корректны
            if not isinstance(updated_user, dict):
                app_logger.warning(
                    "Invalid or missing data for user with tg_id %s : %s",
                    tg_id,
                    updated_user
                )
                return None

            # Добавляем tg_id, если он отсутствует
            if "tg_id" not in updated_user:
                app_logger.warning(
                    "Missing tg_id in user data: %s",
                    updated_user
                )
                updated_user["tg_id"] = tg_id

            # Создаём объект User
            return User(**updated_user)

        except Exception as error:
            app_logger.error("Error updating user role: %s", error)
            raise
