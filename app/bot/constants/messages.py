import datetime
from enum import Enum

from .symbols import Symbols
from typing import Dict, Optional, Type, Union
from aiogram.fsm.state import State


class Messages(Enum):
    WELCOME = f"{Symbols.WAVE.value} Добрый день!"
    GOODBYE = f"{Symbols.WAVE.value} Удачного дня!"
    PLEASE_ENTER = f"{Symbols.LOCK_MANAGER.value} Пожалуйста войдите"
    PLEASE_REGISTER = f"{Symbols.LOCK_MANAGER.value} Пожалуйста зарегистрируйтесь"
    ACCESS_DENIED = (
        f"{Symbols.LOCK_MANAGER.value} Доступ запрещен, обратитесь к администратору."
    )
    USER_NOT_FOUND = f"{Symbols.STATUS_WARNING.value} Пользователь не найден."
    ACCCOUNT_BANNED = f"{Symbols.STATUS_NO.value} Ваш аккаунт заблокирован."
    YOU_ARE_BANNED = f"{Symbols.STATUS_STOP.value} Вы заблокированы."
    INTERNAL_ERROR = f"{Symbols.STATUS_FAIL.value} Внутренняя ошибка."
    USER_NO_PERMISSION = (
        f"{Symbols.STATUS_STOP.value} Недостаточно прав для выполнения этой команды."
    )
    START = (
        f"{Symbols.WAVE.value}"
        + " Привет, {name}!\nДобро пожаловать.\nНажмите кнопку ниже, чтобы войти в систему или пройти регистрацию."
    )
    CANCELLED = f"{Symbols.STATUS_STOP.value}" + " Действие отменено."


TFA_MESSAGES = {
    "prompt": f"{Symbols.USER_LOGIN.value} У вас включена двухфакторная авторизация.\n"
    f"Пожалуйста, введите код подтверждения:",
    "timeout": f"{Symbols.SAND_CLOCK.value} Время ожидания кода истекло. Повторите попытку позже.",
    "fail": f"{Symbols.ACTION_CANCEL.value} Неверный код двухфакторной авторизации.",
    "success": f"{Symbols.ACTION_CONFIRM.value} Успешная авторизация. Продолжаем.",
}

AUTH_MESSAGES = {
    "internal_error": f"{Symbols.STATUS_FAIL.value} Внутренняя ошибка.",
    "no_permission": f"{Symbols.STATUS_STOP} Недостаточно прав для выполнения этой команды.",
    "auth_error": f"{Symbols.STATUS_STOP.value} Ошибка авторизации.",
}
# Сообщения для формы регистрации пользователя

REGISTER_MESSAGES = {
    # 🔹 Ввод ФИО
    "enter_first_name": f"{Symbols.USER_SINGLE.value} Введите ваше имя",
    "enter_last_name": f"{Symbols.USER_SINGLE.value} Введите вашу фамилию",

    # 🔹 Выбор департамента и должности
    "enter_department": f"{Symbols.USER_GROUP.value} Выберите направление / отдел",
    "enter_position": f"{Symbols.USER_ADMIN.value} Выберите должность",

    # 🔹 Локация (если используется участок обслуживания)
    "enter_country": f"{Symbols.USER_GROUP.value} Укажите участок обслуживания",

    # 🔹 Контакт и email
    "enter_phone": f"{Symbols.USER_BROADCAST.value} Отправьте ваш номер телефона (кнопкой ниже)",
    "enter_email": f"{Symbols.USER_LOGIN.value} Введите корпоративную почту",

    # 🔹 Финал
    "success": f"{Symbols.USER_LOGOUT.value} Проверьте введённые данные и подтвердите регистрацию",
}


class HelpCategory(Enum):
    """Категории контекстной помощи"""

    DEFAULT = "default"
    REGISTRATION = "registration"
    PAYMENT = "payment"
    PROFILE = "profile"
    SETTINGS = "settings"
    ORDERS = "orders"
    SUPPORT = "support"


class ContextHelp:
    """Менеджер контекстно-зависимой помощи"""

    _help_messages: Dict[HelpCategory, str] = {
        HelpCategory.DEFAULT: "ℹ️ Основные команды:\n/start - Начало работы\n/help - Помощь\n/cancel - Отмена",
        HelpCategory.REGISTRATION: "📝 Помощь по регистрации:\nЗаполните все поля...",
        HelpCategory.PAYMENT: "💳 Помощь по оплате:\nДоступные способы оплаты...",
        HelpCategory.PROFILE: "👤 Помощь по профилю:\nИзменить данные...",
        HelpCategory.SETTINGS: "⚙️ Помощь по настройкам:\nЯзык, уведомления...",
        HelpCategory.ORDERS: "📦 Помощь по заказам:\nСтатус, история...",
        HelpCategory.SUPPORT: "🆘 Техподдержка:\nКонтакты, часы работы...",
    }

    _state_mapping: Dict[str, HelpCategory] = {
        "registration": HelpCategory.REGISTRATION,
        "payment": HelpCategory.PAYMENT,
        "profile": HelpCategory.PROFILE,
        "settings": HelpCategory.SETTINGS,
        "orders": HelpCategory.ORDERS,
        "support": HelpCategory.SUPPORT,
    }

    @classmethod
    def get_help_for_state(cls, state: Optional[Union[str, State, Type[State]]]) -> str:
        """Возвращает контекстно-зависимое сообщение помощи"""
        if state is None:
            return cls._help_messages[HelpCategory.DEFAULT]

        # Обработка разных типов состояния
        state_str = (
            state.state
            if isinstance(state, State)
            else (
                state.__name__
                if isinstance(state, type) and issubclass(state, State)
                else str(state)
            ).lower()
        )

        # Поиск соответствующей категории помощи
        for key, category in cls._state_mapping.items():
            if key in state_str:
                return cls._help_messages[category]

        return cls._help_messages[HelpCategory.DEFAULT]

    @classmethod
    def get_full_help(cls) -> str:
        """Возвращает полную справку по всем командам"""
        return "\n\n".join(cls._help_messages.values())


class ErrorMessages(Enum):
    NO_EXCEPTION_INFO = (
        "Не удалось обработать исключение: отсутствует информация об ошибке."
    )
    FLOOD_CONTROL = "Слишком много запросов. Попробуйте через {retry_after} секунд."
    UNAUTHORIZED_TOKEN = "Неверный токен бота! Проверьте токен."
    FORBIDDEN_CHAT = "К сожалению, я больше не могу отправлять сообщения в этом чате."
    TOKEN_CONFLICT = "Токен бота используется другим приложением в режиме polling. Проверьте настройки."
    RESOURCE_NOT_FOUND = "Запрошенный ресурс не найден."
    BAD_REQUEST = (
        "Запрос не может быть выполнен. Проверьте корректность введенных данных."
    )
    TELEGRAM_API_ERROR = "Ошибка Telegram API: {exception}"
    UNKNOWN_ERROR_USER = (
        "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."
    )

    @staticmethod
    def error_message(msg=None):
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg_text = msg or "Во время выполнения функции произошла ошибка"
        return (
            f"<b>Ошибка {Symbols.ACTION_ERROR.value}</b> <pre>{msg_text}</pre>\n"
            f"<i>Выполнено: <code>{current_date}</code></i>"
        )
