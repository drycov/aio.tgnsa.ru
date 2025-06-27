from datetime import datetime, timezone
from enum import Enum
from typing import Union

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import logger, settings
from app.core.services.paswword import hash_password
from app.exceptions.exceptions import UserBannedError, UserNotFoundError
from app.models import Role, User
from app.schemas.user import UserCreate


class UserSearchField(str, Enum):
    ID = "id"
    TG_ID = "tg_id"
    ROLE = "role"


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(
        self, value: Union[int, str], field: UserSearchField = UserSearchField.ID
    ) -> User:
        stmt = select(User).options(selectinload(User.roles))
        stmt = stmt.filter(getattr(User, field.value) == value)

        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if not user:
            logger.warning(f"User not found: {field}={value}")
            raise UserNotFoundError(f"{field}={value}")

        if user.is_banned:
            logger.info(f"User is banned: {user.id}")
            raise UserBannedError(f"{user.id}")

        return user

    async def get_all_users(self) -> list[User]:
        result = await self.session.scalars(select(User))
        users = result.all()
        logger.info(f"Fetched {len(users)} users")
        return users

    async def create_user(self, user_data: UserCreate, role_name: str = "user") -> User:
        payload = user_data.model_dump()
        password = payload.pop("password", None)

        new_user = User(**payload)
        # Внутри UserService.create_user()
        if "password" in payload:
            payload["hashed_password"] = hash_password(payload.pop("password"))
        else:
            payload["hashed_password"] = None

        # Attach role, create if needed
        role = (
            await self.session.execute(select(Role).filter_by(name=role_name))
        ).scalar_one_or_none()
        if not role:
            role = Role(name=role_name)
            self.session.add(role)
            await self.session.flush()

        new_user.roles.append(role)
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def ban_user(self, user: User) -> None:
        user.is_banned = True
        user.banned_at = datetime.now(timezone.utc)
        await self.session.commit()
        logger.info(f"User banned: {user.id}")

    async def set_authorized(self, tg_id: int, value: bool) -> None:
        stmt = update(User).where(User.tg_id == tg_id).values(is_authorized=value)
        await self.session.execute(stmt)
        await self.session.commit()

    async def is_admin(self, tgid: int) -> bool:
        return tgid in settings.bot.ADMINS
