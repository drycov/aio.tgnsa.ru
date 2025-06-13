from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.bot.constants.messages import AUTH_MESSAGES


class RoleMiddleware(BaseMiddleware):
    """Middleware, ограничивающий доступ на основе ролей пользователя."""

    def __init__(self, required_roles: list[str], logger):
        self.logger = logger
        self.required_roles = set(required_roles)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("user")

        if not user:
            self.logger.warning(
                "Доступ запрещен: пользователь не найден в данных.")
            await event.answer(AUTH_MESSAGES["auth_error"])
            return

        tg_id = getattr(user, "tg_id", None)

        # 👇 Пропуск проверки ролей, если суперпользователь
        if data.get("is_superuser"):
            self.logger.debug(
                f"🔁 Суперпользователь — пропуск RoleMiddleware для tg_id={tg_id}")
            return await handler(event, data)

        # Инициализация ролей
        user_roles = set()
        roles = getattr(user, "roles", None)
        if roles:
            user_roles = {
                role.name if hasattr(role, "name") else role
                for role in roles
            }
        elif hasattr(user, "role"):
            user_roles = {user.role}

        self.logger.info(
            f"👤 Проверка ролей для tg_id={tg_id}: "
            f"роли={user_roles}, требуется={self.required_roles}"
        )

        if not user_roles.intersection(self.required_roles):
            self.logger.warning(
                f"⛔️ Доступ запрещён: tg_id={tg_id}, роли {user_roles} не соответствуют {self.required_roles}"
            )
            await event.answer(AUTH_MESSAGES["no_permission"])
            return

        return await handler(event, data)
