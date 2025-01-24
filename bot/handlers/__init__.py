# bot/handlers/bot_module.py
from aiogram import Router

# Импортируем все маршрутизаторы, сгруппированные по функциональности
from .admin_handler import admin_router, admin_callback_router,user_mananger
from .advanced_handlers import cidr_router, p2p_router, ping_router, advanced_router
from .device_handlers import check_device_router, device_command_router, device_port_router, vlan_router, ddm_router,lldp_router
from .error_handler import router as error_router
from .ertm_handler import ertm_router, ertm_track
from .main_handlers import main_callback_router, main_commands_router, registration_router
from .message_handler import router as message_router
from .start_handler import router as start_router
from .task_handlers import task_router, task_callback_router

# Собираем список всех маршрутизаторов, с логическим разделением
routers = [
    start_router,  # Стартовый обработчик
    main_callback_router,  # Обработчик основных callback
    task_callback_router,  # Обработчик callback для задач
    admin_callback_router,  #
    check_device_router,  # Обработчик для проверки устройства
    device_command_router,  #
    main_commands_router,  # Основные команды
    message_router,  # Обработчик сообщений
    advanced_router,  # Расширенные модули
    admin_router,  # Обработчик админ-команд
    user_mananger,  # Обработчик управления пользователями
    p2p_router,  # Обработчик для P2P
    cidr_router,  # CIDR-калькулятор
    ping_router,  # Пинг
    registration_router,  # Обработчик регистрации
    task_router,  # Обработчик задач
    device_port_router,  # Обработчик портов устройств
    vlan_router,  # Обработчик VLAN-адресов устройств
    ertm_router,
    ertm_track,
    ddm_router,
    error_router,  # Обработчик ошибок (раскомментируйте при необходимости)
    lldp_router
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
