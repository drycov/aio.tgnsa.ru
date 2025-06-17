from enum import Enum

from .symbols import Symbols


class Messages(Enum):
    WELCOME = f"{Symbols.WAVE.value} Добрый день!"
    GOODBYE = f"{Symbols.WAVE.value} Удачного дня!"
    PLEASE_ENTER = f"{Symbols.LOCK_MANAGER.value} Пожалуйста войдите"
    PLEASE_REGISTER = f"{Symbols.LOCK_MANAGER.value} Пожалуйста зарегистрируйтесь"
    ACCESS_DENIED = f"{Symbols.LOCK_MANAGER.value} Доступ запрещен, обратитесь к администратору."
    USER_NOT_FOUND = f"{Symbols.STATUS_WARNING.value} Пользователь не найден."
    ACCCOUNT_BANNED = f"{Symbols.STATUS_NO.value} Ваш аккаунт заблокирован."
    YOU_ARE_BANNED = f"{Symbols.STATUS_STOP.value} Вы заблокированы."
    INTERNAL_ERROR = f"{Symbols.STATUS_FAIL.value} Внутренняя ошибка."
    USER_NO_PERMISSION = f"{Symbols.STATUS_STOP} Недостаточно прав для выполнения этой команды."


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
    "enter_first_name": f"{Symbols.USER_LOGIN.value} Введите имя",
    "enter_last_name": f"{Symbols.USER_LOGIN.value} Введите фамилию",
    "enter_position": f"{Symbols.USER_LOGIN.value} Введите должность",
    "enter_phone": f"{Symbols.USER_LOGIN.value} Поделитесь контактом, нажав кнопку внизу",
    "enter_email": f"{Symbols.USER_LOGIN.value} Введите корпоративную почту",
    "enter_department": f"{Symbols.USER_LOGIN.value} Введите филиал",
    "enter_country": f"{Symbols.USER_LOGIN.value} Введите участок обслуживания",
    "success": f"{Symbols.ACTION_CONFIRM.value} Успешная регистрация. Продолжаем.",
}
