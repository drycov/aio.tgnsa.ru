from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class RoleMiddleware(BaseMiddleware):
    """Middleware restricting access by user roles.

    Only users having at least one role in required_roles proceed.
    """

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
            self.logger.warning("Доступ запрещен: пользователь не найден в данных.")
            await event.answer("⛔️ Ошибка авторизации.")
            return

        # Поддержка множественных ролей
        user_roles = {role.name if hasattr(role, 'name') else role for role in getattr(user, "roles", [])}
        # fallback для одного атрибута role
        if not user_roles and hasattr(user, "role"):
            user_roles = {user.role}

        if not user_roles.intersection(self.required_roles):
            self.logger.warning(f"Доступ запрещен пользователю id={getattr(user, 'id', 'unknown')}: "
                                f"роли {user_roles} не входят в требуемые {self.required_roles}")
            await event.answer("⛔️ Недостаточно прав для выполнения этой команды.")
            return

        return await handler(event, data)
