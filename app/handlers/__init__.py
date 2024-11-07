# bot/handlers/bot_module.py
from aiogram import Router

from .admin_approval import router as admin_router
from .advanced_handler import router as advanced_router  #
from .callback_query_handlers import router as callback_router
from .error_handler import router as error_router  # Подключение обработчика ошибок
from .message_handler import router as message_router
from .registration_handler import router as registration_router
from .start_handler import router as start_router
from .test_handler import router as test_router


# Объединяем все маршрутизаторы
def get_handlers_router():
    router = Router()
    router.include_router(callback_router)  # Добавляем маршрутизаторы для обратных вызовов
    router.include_router(test_router)  # Добавляем маршрутизаторы для различных модулей
    router.include_router(start_router)
    router.include_router(message_router)
    router.include_router(advanced_router)  # Добавляем маршрутизаторы для расширенных модулей
    # router.include_router(error_router)  # Добавляем обработчик ошибок
    router.include_router(registration_router)
    router.include_router(admin_router)
    return router
