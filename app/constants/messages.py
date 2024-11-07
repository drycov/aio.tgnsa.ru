from enum import Enum

from .symbols import Symbols


class Messages(Enum):
    # Приветствия и прощания
    WELCOME = f"{Symbols.EMOJI_WAVE.value} Добрый день!"
    GOODBYE = f"{Symbols.EMOJI_WAVE.value} Удачного дня!"

    # Общие сообщения
    JUST_TEXT_NOT_FOUND = f"{Symbols.STATUS_CRITICAL.value} Не найдено. Проверьте ввод или введите команду /help"
    USER_ACCESS_DENIED = "В качестве информации просьба указывать ФИО и должность"

    # Помощь и информация
    HELP = (
        f"<b>{Symbols.ROLE_USER.value} Команды пользователя</b>\n"
        f"<i><code>/help</code> - вызвать это сообщение</i>\n"
        f"<i><code>/start</code> - запуск сервиса</i>\n"
        f"<i><code>/info</code> - информация о сервисе</i>\n"
        f"<i><s><code>/descr</code> - описание функционала сервиса</s>\n"
        f"<s><code>/admins</code> - контакты Администраторов сервиса</s></i>"
    )
    DESCRIPTION = (
        "Бот создан для автоматизации процессов ТТС.\n"
        "Здесь вы можете проверить состояние оборудования доступа.\n"
        "В данный момент бот находится на стадии разработки.\n"
        "Доступна только функция проверки статуса портов."
    )

    # Доступ и регистрация
    REGISTER = f"{Symbols.EMOJI_WAVE.value} Добрый день! Для работы с системой введите ваш корпоративный E-Mail"
    PLEASE_ENTER = f"{Symbols.EMOJI_LOCK_MANAGER.value} Пожалуйста войдите"
    ACCESS_DENIED = f"{Symbols.EMOJI_LOCK_MANAGER.value} Доступ запрещен, обратитесь к администратору."
    USER_SAVED_IN_DB = f"{Symbols.OK.value} Вы добавлены в базу. {Symbols.EMOJI_SAND_CLOCK.value} Ожидайте одобрения."

    USER_ALLOWED_IN_DB = (
        f"{Symbols.OK.value} Вы добавлены в базу. {Symbols.OK.value} "
        f"Для начала работы введите /start или {Symbols.INDICATOR_GREEN.value} Войти."
    )
    USER_REMOVED_FROM_DB = f"{Symbols.OK.value} Вы удалены из базы."
    USER_REJECTED_FROM_DB = f"{Symbols.INDICATOR_RED.value} Ваш доступ отклонен администратором"
    NOT_REGISTERED=f"{Symbols.EMOJI_LOCK_MANAGER.value} Вы не зарегистрированы в системе."

    # Сообщения API токена
    API_TOKEN_CREATION = f"{Symbols.EMOJI_LOCK_MANAGER.value} Создается токен-доступа в приложение"
    API_TOKEN_CREATED = f"{Symbols.OK.value} Ваш токен создан:"

    # Сообщения для IP и подсети
    ENTER_IP = "Введите IP-адрес устройства."
    ENTER_SUBNET_P2P = "Введите IP-адрес в формате <i><code>A.B.C.D/Mask(30)</code></i>."
    ENTER_SUBNET = "Введите IP-адрес в формате <i><code>A.B.C.D/Mask(0-32)</code></i>."

    # Сообщения об ошибках
    ERROR_SUBNET = f"{Symbols.CABLE_SHORT.value} Это не CIDR. Укажите IP в формате A.B.C.D / Mask(0 - 32) и повторите."
    ERROR_P2P = f"{Symbols.CABLE_SHORT.value} Это не P2P. Укажите IP в формате A.B.C.D / Mask(30) и повторите."
    ERROR_NO_ACL = f"{Symbols.STATUS_WARNING.value} Нет прав"
    ERROR_ACTION = "Нет прав для доступа в меню:"
    ERROR_GENERAL = f"<b>{Symbols.STATUS_CRITICAL.value} Произошла ошибка, попробуйте позже!</b>"
    ERROR_SNMP = (
        f"<b>{Symbols.CABLE_SHORT.value} Устройство не на связи или при выполнении задачи произошла ошибка!</b>\n"
        f"<i>Попробуйте позже.</i>\n"
        f"<code>Возможно у сервиса нет прав на опрос оборудования или значение SNMP readonly Community не равно public.</code>"
    )

    # Легенда для статуса порта
    PORT_LEGEND = (
        f"Включен: {Symbols.OK.value} "
        f"Отключен: {Symbols.STATUS_DISCONNECTED.value} "
        f"Выключен: {Symbols.STATUS_OFFLINE.value} "
        f"Не опр.: {Symbols.STATUS_UNKNOWN.value}"
    )

    # Администрирование
    USER_ADDED = f"{Symbols.OK.value} Пользователь добавлен"
    USER_REMOVED = f"{Symbols.OK.value} Пользователь удален"
    USER_UPDATED = f"{Symbols.OK.value} Пользователь изменен"
    USER_REJECTED = f"{Symbols.STATUS_WARNING.value} Пользователь отклонен"
    ADMIN_HELP = (
        f"<b>{Symbols.TECH_LAB.value} Команды Администратора</b>\n"
        f"<i><code>/log</code> - выгрузка логов</i>\n"
        f"<i><code>/si</code> - служебная информация</i>\n"
        f"<i><code>/enb_'ID'</code> - подтвердить доступ для пользователя с 'ID'</i>\n"
        f"<i><code>/dsb_'ID'</code> - отозвать доступ</i>\n"
        f"<i><code>/yadm_'ID'</code> - предоставить доступ администратора</i>\n"
        f"<i><code>/nadm_'ID'</code> - отозвать доступ администратора</i>\n"
        f"<i><code>/ui_'ID'</code> - профиль пользователя c 'ID'</i>"
    )

    # Сообщения для массовых инцидентов
    MASS_INCIDENT_STATION = "Введите название станции(й):"
    MASS_INCIDENT_CITY = "Введите название города(ов):"
    MASS_INCIDENT_ADDRESS = "Введите адрес(а):"
    MASS_INCIDENT_CAUSE = "Введите причину:"
    MASS_INCIDENT_FROM = "Введите Должность, Фамилию, Имя"
    MASS_INCIDENT_PHONE = "Введите контактный телефон:"
    MASS_INCIDENT_PRIORITY = "Введите приоритет:"
    MASS_INCIDENT_END_TIME = "Введите ориентировочное время завершения инцидента:"

    # Сообщения для формы регистрации пользователя
    REGISTER_FIRST_NAME = "Введите имя"
    REGISTER_LAST_NAME = "Введите фамилию"
    REGISTER_POSITION = "Введите должность"
    REGISTER_PHONE = "Поделитесь контактом, нажав кнопку внизу"
    REGISTER_EMAIL = "Введите корпоративную почту"
    REGISTER_DEPARTMENT = "Введите филиал"
    REGISTER_COUNTRY = "Введите участок обслуживания"

    # Сообщения для массовой рассылки
    MASS_MAIL_SUBJECT = "Введите тему:"
    MASS_MAIL_MESSAGE = "Введите ваше сообщение:"
    MASS_MAIL_ONLY_ADMINS = "Только для админов?"
    MASS_MAIL_PRIORITY = "Выберите приоритет"
    MASS_MAIL_DEPARTMENT = "Выберите филиал"
    MASS_MAIL_CAUSE = "Введите причину:"
    MASS_MAIL_FROM_BOT = "Рассылка от имени бота?"

    # Сообщения для старта и завершения работы бота
    START_BOT_MODULE = "Запуск основного модуля бота..."
    START_BOT = "Бот запущен и работает."
    SHUTDOWN_BOT = "Запуск процедуры завершения работы бота..."
    SHUTDOWN_SIGNAL = "Получен сигнал завершения, бот отключается..."
    DELETE_WEBHOOK = "Удаление вебхука и запуск поллинга..."
    BOT_SHUTDOWN_COMPLETE = "Бот завершил работу корректно."


class LogMessages(Enum):
    LOGGER_INITIALIZED = "Логгер инициализирован."
    SNMP_ERROR = "Ошибка SNMP: {error}"
    SNMP_UNAVAILABLE = "{host} SNMP недоступен"
    ACTION_FAILED = "Действие {action} завершилось с ошибкой для хоста {host} и OID {oid}"
    UNKNOWN_ERROR = "Произошла неизвестная ошибка: {error}"
    FILE_NOT_FOUND = "Файл {file_path} не найден."
    JSON_DECODE_ERROR = "Ошибка декодирования JSON в файле {file_path}"
    DATA_LOADED = "Загружены данные из файла {file_path}"
    DEVICE_DATA_LOADED = "Загружены данные устройства из файла {file_path}"
    MODEL_FILTERED = "Модель устройства '{model_name}' найдена для ключа '{model_key}'"
    MODEL_NOT_FOUND = "Модель устройства для данных '{dirty_data}' не найдена."
    CONFIG_NOT_FOUND = "Конфигурация для модели '{model_key}' не найдена, возвращаются значения по умолчанию."
    FILTERING_MODEL = "Фильтрация модели устройства для данных: {dirty_data}"


class ErrorMessages(Enum):
    NO_EXCEPTION_INFO = "Не удалось обработать исключение: отсутствует информация об ошибке."
    FLOOD_CONTROL = "Слишком много запросов. Попробуйте через {retry_after} секунд."
    UNAUTHORIZED_TOKEN = "Неверный токен бота! Проверьте токен."
    FORBIDDEN_CHAT = "К сожалению, я больше не могу отправлять сообщения в этом чате."
    TOKEN_CONFLICT = "Токен бота используется другим приложением в режиме polling. Проверьте настройки."
    RESOURCE_NOT_FOUND = "Запрошенный ресурс не найден."
    BAD_REQUEST = "Запрос не может быть выполнен. Проверьте корректность введенных данных."
    TELEGRAM_API_ERROR = "Ошибка Telegram API: {exception}"
    UNKNOWN_ERROR_USER = "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."


class NetworkMessages(Enum):
    ERROR_SUBNET_CALCULATION = "Ошибка в вычислении подсети: {error}"
    ERROR_P2P_CALCULATION = "Ошибка в вычислении P2P: {error}"
    ERROR_PING = "Ошибка при выполнении ping: {error}"
    ERROR_FILE_READ = "Ошибка при чтении файла {file_path}: {error}"
    ERROR_SUBNET_FORMAT = "Ошибка в формате адреса сети."
    ERROR_P2P_FORMAT = "Ошибка в формате P2P адреса."
    NETWORK_INFO = (
        "Адрес сети: <code>{network}</code>\n"
        "Маска подсети: <code>{netmask}</code>\n"
        "Первый хост: <code>{first}</code>\n"
        "Последний хост: <code>{last}</code>\n"
        "Хостов/Сетей: <code>{size}</code>"
    )
    P2P_INFO = (
        "Хост: <code>{host}</code>\n"
        "Шлюз: <code>{gateway}</code>\n"
        "Маска подсети: <code>{netmask}</code>"
    )
