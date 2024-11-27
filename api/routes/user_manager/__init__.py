from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models import User
from app.utils.logger_instance import app_logger

UserManager = APIRouter()


class UserResponse(BaseModel):
    success: bool
    message: str
    updated_user: User  # Используйте вашу модель `User`


@UserManager.get("/users/", response_model=List[User])
async def get_users() -> List[User]:
    """
    Получение списка всех пользователей.
    """
    try:
        # Импорт сервиса для работы с пользователями
        from api.services import UserService

        # Вызов метода для получения всех пользователей
        users = await UserService.get_all_users()  # Если `UserService` асинхронный
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка пользователей: {e}")


@UserManager.get("/user/{id}", response_model=User)
async def get_user(id: int) -> User:
    """
    Получение пользователя по ID.
    """
    try:
        # Вызов метода для получения пользователя по ID
        user = User.get_by_tg_id(tg_id=id)  # Если `UserService` асинхронный

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден.")

        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения пользователя по ID: {e}")


@UserManager.put("/user/{id}", response_model=UserResponse)
async def update_user(id: int, updates: dict):
    """
    Обновление данных пользователя по ID.
    """
    try:
        if not updates:
            raise HTTPException(status_code=400, detail="Запрос на обновление пуст.")
        print(f"Updates: {updates}")
        # Обновляем данные пользователя в Firebase
        updated_user = User.update(tg_id=id, updates=updates)

        if not updated_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден или данные некорректны.")

        return UserResponse(
            success=True,
            message=f"Пользователь с ID {id} обновлен.",
            updated_user=updated_user
        )

    except HTTPException as e:
        # Если уже сгенерирован HTTPException, пробрасываем
        raise e
    except Exception as e:
        # Логирование ошибки
        app_logger.error(f"Ошибка обновления пользователя {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления пользователя: {e}")


@UserManager.delete("/user/{id}")
async def delete_user(id: int):
    """
    Добавление или обновление данных пользователя по ID.
    """
    try:
        # Преобразование объекта `User` в словарь

        # Добавляем или обновляем пользователя в Firebase
        User.delete(tg_id=id)
        return {"message": f"Пользователь с ID {id} успешно удалён."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления пользователя: {e}")
