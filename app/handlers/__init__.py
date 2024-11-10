# bot/handlers/bot_module.py
from aiogram import Router

from .admin_approval import router as admin_router
from .advanced_handler import router as advanced_router
from .advanced_handlers import cidr_router, p2p_router, ping_router
from .callback_query_handlers import router as callback_router
from .error_handler import router as error_router
from .message_handler import router as message_router
from .registration_handler import router as registration_router
from .shedule_handlers import task_router
from .start_handler import router as start_router
from .test_handler import router as test_router

# Создаем список всех маршрутизаторов
routers = [
    start_router,
    callback_router,  # Обратные вызовы
    message_router,
    advanced_router,  # Расширенные модули
    admin_router,
    p2p_router,
    cidr_router,  # CIDR калькулятор
    ping_router,  # Пинг
    test_router,  # Различные модули
    # error_router,  # Обработчик ошибок (раскомментируйте при необходимости)
    registration_router,
    task_router,
]


# Функция для объединения маршрутизаторов
def get_handlers_router():
    router = Router()
    for r in routers:
        router.include_router(r)
    return router
