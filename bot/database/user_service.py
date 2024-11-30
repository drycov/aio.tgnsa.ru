from bot.models import User
from bot.utils.logger_instance import app_logger


def handle_error(message: str, data: str, error: Exception):
    message += f'"data":"{data}", "error":"{error}"'
    app_logger.error(message)
    raise error


def handle_result_not_found(message: str, status: str, description: str = None):
    message += f'"status":"{status}"'
    if description:
        message += f', "description":"{description}"'
    app_logger.error(message)


async def save_user(user_data: dict) -> int | str:
    """
    Сохраняет нового пользователя в базе данных.
    """
    try:
        user = User.create(user_data)
        return user.tg_id
    except Exception as error:
        handle_error("Error saving user", str(user_data), error)
        return ''


async def get_all_users() -> list:
    """
    Получает всех пользователей.
    """
    try:
        return [user.model_dump() for user in User.get_all()]
    except Exception as error:
        handle_error("Error fetching all users", "get_all_users", error)
        return []


async def get_user_by_tg_id(tg_id: int) -> dict | None:
    """
    Получает пользователя по tg_id.
    """
    try:
        user = User.get_by_tg_id(tg_id)
        return user.model_dump() if user else None
    except Exception as error:
        handle_error("Error fetching user by tg_id", str(tg_id), error)
        return None


async def get_admin_users() -> list:
    """
    Получает список всех администраторов.
    """
    try:
        return [admin.model_dump() for admin in User.get_admin_users()]
    except Exception as error:
        handle_error("Error fetching admin users", "get_admin_users", error)
        return []


async def update_user(tg_id: int, updated_user_data: dict) -> dict | None:
    """
    Обновляет данные пользователя по tg_id.
    """
    try:
        user = User.get_by_tg_id(tg_id)
        if not user:
            handle_result_not_found("User not found", "updateUser", f"User with id {tg_id} not found")
            return None

        user.update(updated_user_data)
        return user.model_dump()
    except Exception as error:
        handle_error("Error updating user", str(tg_id), error)
        return None
