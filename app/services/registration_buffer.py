# app/services/registration_buffer.py
from typing import Dict, Optional


class RegistrationBuffer:
    _storage: Dict[int, dict] = {}

    @classmethod
    async def set(cls, user_id: int, data: dict):
        cls._storage[user_id] = data

    @classmethod
    async def get(cls, user_id: int) -> Optional[dict]:
        return cls._storage.get(user_id)

    @classmethod
    async def delete(cls, user_id: int):
        cls._storage.pop(user_id, None)
