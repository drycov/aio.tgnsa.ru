# app/api/routes/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session  # генератор сессии
from app.schemas.user import UserCreate, UserResponse  # схема ответа
from app.services.user import UserSearchField, UserService

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
async def list_users(
    session: AsyncSession = Depends(get_session),
):
    user_service = UserService(session)
    return await user_service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    user_service = UserService(session)
    user = await user_service.get_user(user_id, UserSearchField.ID)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_tg_id(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    user_service = UserService(session)
    user = await user_service.get_user(user_id, UserSearchField.TG_ID)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,  # схема создания пользователя
        session: AsyncSession = Depends(get_session),

):
    user_service = UserService(session)
    return await user_service.create_user(user_data)
