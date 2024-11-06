# bot/handlers/__init__.py
from aiogram import Router
from .start_handler import router as start_router
from .message_handler import router as message_router
from .error_handler import router as error_router  # Подключение обработчика ошибок


# Объединяем все маршрутизаторы
def get_handlers_router():
    router = Router()
    router.include_router(start_router)
    router.include_router(message_router)
    router.include_router(error_router)  # Добавляем обработчик ошибок

    return router
