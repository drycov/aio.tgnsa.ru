import re


class RegExpUtils:
    """Класс для работы с регулярными выражениями и проверками."""

    def __init__(self, bot_name: str = ""):
        # Инициализация регулярного выражения для имени бота, если указано
        self.bot_name = bot_name
        self.bot_name_pattern = self.create_bot_name_regexp(bot_name) if bot_name else None

        # Регулярные выражения
        self.ip_regexp = self.create_regexp(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$")
        self.subnet_regexp = self.create_regexp(r"^(\d+\.\d+\.\d+\.\d+)(/\d+)$")
        self.p2p_subnet_regexp = self.create_regexp(r"^(\d+\.\d+\.\d+\.\d+)(/30)$")
        self.user_grant_regexp = self.create_regexp(r"/enb_")
        self.user_revoke_regexp = self.create_regexp(r"/dsb_")
        self.admin_grant_regexp = self.create_regexp(r"/yadm_")
        self.admin_revoke_regexp = self.create_regexp(r"/nadm_")
        self.user_info_regexp = self.create_regexp(r"/ui_")
        self.email_regexp = self.create_regexp(r"[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]+")
        self.ttc_email_regexp = self.create_regexp(r"[a-zA-Z0-9]+@ttc.kz")

    @staticmethod
    def create_regexp(pattern: str, flags: int = 0) -> re.Pattern:
        """Создает регулярное выражение с заданным шаблоном и флагами."""
        return re.compile(pattern, flags)

    def create_bot_name_regexp(self, bot_name: str) -> re.Pattern:
        """Создает регулярное выражение для имени бота."""
        return self.create_regexp(rf"\@{bot_name}\s")

    def create_substring_replacer(self):
        """Создает функцию для удаления имени бота из строки."""
        if not self.bot_name_pattern:
            raise ValueError("Имя бота не задано для создания функции замены.")
        return lambda value: self.bot_name_pattern.sub("", value.strip())

    @staticmethod
    def create_check_function(regexp: re.Pattern):
        """Создает функцию проверки для заданного регулярного выражения."""
        return lambda value: bool(regexp.fullmatch(value.strip()))

    # Методы для выполнения проверок
    def ip_check(self, value: str) -> bool:
        return self.create_check_function(self.ip_regexp)(value)

    def subnet_check(self, value: str) -> bool:
        return self.create_check_function(self.subnet_regexp)(value)

    def p2p_check(self, value: str) -> bool:
        return self.create_check_function(self.p2p_subnet_regexp)(value)

    def email_check(self, value: str) -> bool:
        return self.create_check_function(self.email_regexp)(value)

    def ttc_email_check(self, value: str) -> bool:
        return self.create_check_function(self.ttc_email_regexp)(value)
