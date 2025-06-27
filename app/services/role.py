from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role
from app.models.user import User
from app.core.config import logger


class RoleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_default_roles(self) -> None:
        """
        Создаёт базовые роли, если их ещё нет.
        Выполняет один запрос + flush при необходимости.
        """
        default = set(Role.default_roles())
        rows = await self.session.execute(select(Role.name))
        existing = {row[0] for row in rows.all()}
        to_create = default - existing

        for name in to_create:
            role = Role(name=name)
            self.session.add(role)
            logger.info(f"Добавлена роль: {name}")

        if to_create:
            await self.session.flush()

    async def get_role(self, name: str, create_if_missing: bool = False) -> Role:
        """
        Возвращает роль по имени.
        Если create_if_missing=True, создаёт новую роль при отсутствии.
        """
        role = await self.session.scalar(select(Role).filter_by(name=name))
        if role:
            return role

        if create_if_missing:
            role = Role(name=name)
            self.session.add(role)
            await self.session.flush()
            logger.info(f"Создана новая роль '{name}'")
            return role

        logger.warning(f"Роль не найдена: '{name}'")
        raise NoResultFound(f"Role '{name}' not found")

    async def assign_role(
        self, user: User, role_name: str, commit: bool = False
    ) -> None:
        """
        Назначает роль пользователю. Создаёт роль, если её нет.
        Использует ассоциацию many-to-many через relationship.
        """
        role = await self.get_role(role_name, create_if_missing=True)

        if role in user.roles:
            logger.debug(f"Пользователь id={user.id} уже имеет роль '{role_name}'")
            return

        user.roles.append(role)
        logger.info(f"Добавлена роль '{role_name}' пользователю id={user.id}")

        if commit:
            await self.session.commit()

    async def remove_role(
        self, user: User, role_name: str, commit: bool = False
    ) -> None:
        """
        Снимает роль с пользователя, если она есть.
        """
        role = await self.get_role(role_name)  # выбросит, если роли нет
        if role in user.roles:
            user.roles.remove(role)
            logger.info(f"Роль '{role_name}' удалена у пользователя id={user.id}")
            if commit:
                await self.session.commit()
        else:
            logger.debug(f"Пользователь id={user.id} не имел роль '{role_name}'")

    async def list_user_roles(self, user: User) -> list[str]:
        """Возвращает список имён ролей пользователя."""
        return [role.name for role in user.roles]
