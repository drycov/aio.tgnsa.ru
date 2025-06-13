"""
Модуль API маршрутов FastBill.

Этот модуль содержит все API маршруты приложения, организованные по подмодулям:
- auth: Аутентификация и авторизация
- users: Управление пользователями
- billing: Биллинг и платежи
- reports: Отчеты и статистика
- system: Системные операции

Структура:
├── auth/
│   ├── routes.py - Маршруты аутентификации
│   └── dependencies.py - Зависимости для авторизации
├── users/
│   ├── routes.py - CRUD операции пользователей
│   └── models.py - Pydantic модели пользователей
└── root.py - Корневые маршруты и документация API

Использование:
    from app.api.users import router as users_router
    app.include_router(users_router, prefix="/api/users", tags=["users"])

Примечания:
    - Все маршруты используют стандартный формат ответа
    - Поддерживается валидация через Pydantic
    - Включена автоматическая документация OpenAPI
    - Реализовано логирование запросов
"""

from .users import router as users_router
# from .auth import auth_router
from .root import router as root_router
from fastapi import APIRouter

# Создаем корневой роутер
api_router = APIRouter()

# Импортируем и подключаем все подмодули
api_router.include_router(root_router)

# api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

api_router.include_router(users_router, prefix="/users", tags=["users"])

# Для удобства импорта
__all__ = ["api_router"]