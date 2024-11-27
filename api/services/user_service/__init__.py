from typing import Optional

from firebase_admin import db
from pydantic import ValidationError

from app.models import User
from app.utils.logger_instance import app_logger


class UserService:

    @staticmethod
    async def get_all_users() -> list[User]:
        """
        Получает список всех пользователей из Firebase с обработкой ошибок.
        """
        try:
            return User.get_all()
        except Exception as error:
            app_logger.error("Error fetching all users: %s", error)
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

    @staticmethod
    def delete_user(tg_id: int) -> None:
        """
        Удаляет пользователя по tg_id.
        """
        try:
            user_ref = db.reference(f'users/{tg_id}')
            user_ref.delete()
        except Exception as e:
            app_logger.error("Error deleting user with tg_id %s: %s", tg_id, e)
            raise

    @staticmethod
    def get_admin_users() -> list[User]:
        """
        Получает список всех администраторов.
        """
        pass

    @staticmethod
    def get_user_by_tg_id(tg_id: int) -> Optional[User]:
        """
        Получает пользователя по tg_id.
        """
        pass