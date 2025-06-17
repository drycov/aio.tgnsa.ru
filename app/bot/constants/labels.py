from enum import Enum


class MenuLabels(Enum):
    DEVICE_CHECK = "🧪 Проверка устройства"
    ADVANCED = "🛠 Дополнительно"
    ERTM_MENU = "📡 Подсистема ЭРТМ"
    TASK_MANAGER = "📋 Задачи"
    USER_PROFILE = "👤 Профиль"
    EXIT = "🚪 Выход"
    SHARE_CONTACT = "📞 Поделиться контактом"

    ADMIN_PANEL = "🛠 Админ-панель"
    VIEW_USERS = "👥 Пользователи"
    SEND_BROADCAST = "📢 Рассылка"
    SYSTEM_STATUS = "📊 Статус системы"

    CHECK_COMPONENTS = "🔍 Проверить компоненты"
    RESTART_CHECKS = "🔄 Перезапустить проверки"
    GET_LOGS = "📜 Получить логи"

    BACK = "⬅️ Назад"
