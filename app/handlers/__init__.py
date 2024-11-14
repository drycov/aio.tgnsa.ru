# bot/handlers/bot_module.py
from aiogram import Router

# Импортируем все маршрутизаторы, сгруппированные по функциональности
from .admin_handler import admin_router, admin_callback_router
from .advanced_handlers import cidr_router, p2p_router, ping_router, advanced_router
from .device_handlers import check_device_router, device_command_router
from .error_handler import router as error_router
from .main_handlers import main_callback_router, main_commands_router, registration_router
from .message_handler import router as message_router
from .start_handler import router as start_router
from .task_handlers import task_router, task_callback_router
from .test_handler import router as test_router

# Собираем список всех маршрутизаторов, с логическим разделением
routers = [
    start_router,  # Стартовый обработчик
    main_callback_router,  # Обработчик основных callback
    task_callback_router,  # Обработчик callback для задач
    admin_callback_router, #
    check_device_router, # Обработчик для проверки устройства
    device_command_router, #
    main_commands_router,  # Основные команды
    message_router,  # Обработчик сообщений
    advanced_router,  # Расширенные модули
    admin_router,  # Обработчик админ-команд
    p2p_router,  # Обработчик для P2P
    cidr_router,  # CIDR-калькулятор
    ping_router,  # Пинг
    test_router,  # Тестовые модули
    # error_router, # Обработчик ошибок (раскомментируйте при необходимости)
    registration_router,  # Обработчик регистрации
    task_router  # Обработчик задач
]


# Функция для объединения маршрутизаторов
def get_handlers_router():
    main_router = Router()
    for router in routers:
        if isinstance(router, Router):
            main_router.include_router(router)
        else:
            raise ValueError(f"Элемент {router} не является экземпляром Router")
    return main_router
