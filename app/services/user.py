# app/services/user.py
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, tg_id: int):
        # Реализация бизнес-логики получения пользователя
        pass