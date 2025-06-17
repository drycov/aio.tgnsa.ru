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
        """Добавляет базовые роли (admin, moderator, user), если их нет."""
        default = set(Role.default_roles())
        stmt = select(Role.name)
        rows = await self.session.execute(stmt)
        existing = {row[0] for row in rows.all()}
        to_add = default - existing

        for name in to_add:
            self.session.add(Role(name=name))
            logger.info(f"Добавлена роль: {name}")

        if to_add:
            await self.session.flush()

    async def get_role(self, name: str, create_if_missing: bool = False) -> Role:
        """Возвращает роль по имени, опционально создаёт новую."""
        role = await self.session.scalar(select(Role).filter_by(name=name))
        if role:
            return role

        if create_if_missing:
            role = Role(name=name)
            self.session.add(role)
            await self.session.flush()
            logger.info(f"Создана неизвестная роль '{name}'")
            return role

        logger.warning(f"Роль не найдена: '{name}'")
        raise NoResultFound(f"Role '{name}' not found")

    async def assign_role(self, user: User, role_name: str, commit: bool = False) -> None:
        """
        Назначает роль пользователю.
        Если роли нет в БД — создаёт её.
        """
        role = await self.get_role(role_name, create_if_missing=True)

        if role not in user.roles:
            user.roles.append(role)
            logger.info(f"Роль '{role_name}' добавлена пользователю id={user.id}")
            if commit:
                await self.session.commit()
        else:
            logger.debug(f"Пользователь id={user.id} уже имеет роль '{role_name}'")

    async def remove_role(self, user: User, role_name: str, commit: bool = False) -> None:
        """Убирает у пользователя роль (если есть)."""
        role = await self.get_role(role_name)
        if role in user.roles:
            user.roles.remove(role)
            logger.info(f"Роль '{role_name}' удалена у пользователя id={user.id}")
            if commit:
                await self.session.commit()
        else:
            logger.debug(f"Пользователь id={user.id} не имел роли '{role_name}'")

    async def list_user_roles(self, user: User) -> list[str]:
        """Возвращает имена ролей пользователя."""
        return [role.name for role in user.roles]
