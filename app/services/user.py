from datetime import datetime, timezone
from enum import Enum
from typing import Union

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import logger
from app.core.services.paswword import hash_password
from app.exceptions.exceptions import UserBannedError  # Кастомные исключения
from app.exceptions.exceptions import UserNotFoundError
from app.models import Role, User
from app.schemas.user import UserCreate


class UserSearchField(str, Enum):
    ID = "id"
    TG_ID = "tg_id"


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(
        self, value: Union[int, str], field: UserSearchField = UserSearchField.ID
    ) -> User | None:
        logger.info(f"Поиск пользователя по полю {field} со значением {value}")
        try:
            match field:
                case UserSearchField.ID:
                    stmt = select(User).where(User.id == value)
                case UserSearchField.TG_ID:
                    stmt = select(User).where(User.tg_id == value)
                case _:
                    raise ValueError(f"Unsupported search field: {field}")

            # Подключаем eager loading ролей
            stmt = stmt.options(selectinload(User.roles))

            result = await self.session.execute(stmt)
            user = result.unique().scalar_one_or_none()

            if user:
                logger.info(
                    f"Пользователь найден: id={user.id}, tg_id={user.tg_id}, роли={', '.join([r.name for r in user.roles])}")
            else:
                logger.warning(f"Пользователь не найден по {field} = {value}")

            return user
        except Exception as e:
            logger.exception(f"Ошибка при поиске пользователя: {e}")
            raise

    async def get_all_users(self) -> list[User]:
        logger.info("Получение всех пользователей из базы данных")
        try:
            stmt = select(User)
            result = await self.session.execute(stmt)
            users = result.unique().scalars().all()
            logger.info(f"Получено пользователей: {len(users)}")
            return users
        except Exception as e:
            logger.exception(f"Ошибка при получении списка пользователей: {e}")
            raise

    async def create_user(self, user_data: UserCreate, role_name: str = "user") -> User:
        # 1. Хешируем пароль
        data = user_data.model_dump()
        data['hashed_password'] = hash_password(data.pop('password'))

        # 2. Ищем роль в базе
        stmt = select(Role).where(Role.name == role_name)
        result = await self.session.execute(stmt)
        role = result.scalar_one_or_none()

        # 3. Если роли нет, создаём
        if not role:
            role = Role(name=role_name)
            self.session.add(role)
            await self.session.flush()  # flush чтобы получить id роли

        # 4. Создаём пользователя с ролью
        new_user = User(**data)
        new_user.roles.append(role)

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user
