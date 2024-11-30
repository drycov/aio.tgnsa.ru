"""
This module provides utilities for working with regular expressions, including validation and pattern matching.
"""

import re


class RegExpUtils:
    """Класс для работы с регулярными выражениями и проверками."""

    def __init__(self, bot_name: str = ""):
        """
        Initializes the RegExpUtils class with precompiled regular expressions.

        Args:
            bot_name (str): The bot name to include in pattern matching.
        """
        self.bot_name = bot_name
        self.bot_name_pattern = self.create_bot_name_regexp(bot_name) if bot_name else None

        self.regex_patterns = {
            "ip": self.create_regexp(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$"),
            "subnet": self.create_regexp(r"^(\d+\.\d+\.\d+\.\d+)(/\d+)$"),
            "subnet_24": self.create_regexp(r"^(\d+\.\d+\.\d+\.\d+)(/24)$"),
            "p2p_subnet": self.create_regexp(r"^(\d+\.\d+\.\d+\.\d+)(/30)$"),
            "user_grant": self.create_regexp(r"/enb_"),
            "user_revoke": self.create_regexp(r"/dsb_"),
            "admin_grant": self.create_regexp(r"/yadm_"),
            "admin_revoke": self.create_regexp(r"/nadm_"),
            "user_info": self.create_regexp(r"/ui_"),
            "email": self.create_regexp(r"[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]+"),
            "ttc_email": self.create_regexp(r"[a-zA-Z0-9]+@ttc.kz"),
            "dlink": self.create_regexp(r"Port \d+"),
        }

    @staticmethod
    def create_regexp(pattern: str, flags: int = 0) -> re.Pattern:
        """Создает регулярное выражение с заданным шаблоном и флагами."""
        return re.compile(pattern, flags)

    def create_bot_name_regexp(self, bot_name: str) -> re.Pattern:
        """Создает регулярное выражение для имени бота."""
        return self.create_regexp(rf"\@{bot_name}\s")

    def create_substring_replacer(self):
        """
        Creates a function to remove the bot name from a string.

        Returns:
            Callable[[str], str]: A function to replace the bot name.
        """
        if not self.bot_name_pattern:
            raise ValueError("Имя бота не задано для создания функции замены.")
        return lambda value: self.bot_name_pattern.sub("", value.strip())

    @staticmethod
    def create_check_function(regexp: re.Pattern):
        """
        Creates a function to check if a value matches a regular expression.

        Args:
            regexp (re.Pattern): The compiled regular expression.

        Returns:
            Callable[[str], bool]: A function to check the value.
        """
        return lambda value: bool(regexp.fullmatch(value.strip()))

    # Методы для выполнения проверок
    def ip_check(self, value: str) -> bool:
        """Checks if the given value is a valid IP address."""
        return self.create_check_function(self.regex_patterns["ip"])(value)

    def subnet_check(self, value: str) -> bool:
        """Checks if the given value is a valid subnet."""
        return self.create_check_function(self.regex_patterns["subnet"])(value)

    def subnet_24_check(self, value: str) -> bool:
        """Checks if the given value is a valid /24 subnet."""
        return self.create_check_function(self.regex_patterns["subnet_24"])(value)

    def p2p_check(self, value: str) -> bool:
        """Checks if the given value is a valid /30 subnet."""
        return self.create_check_function(self.regex_patterns["p2p_subnet"])(value)

    def email_check(self, value: str) -> bool:
        """Checks if the given value is a valid email address."""
        return self.create_check_function(self.regex_patterns["email"])(value)

    def ttc_email_check(self, value: str) -> bool:
        """Checks if the given value is a valid TTC email address."""
        return self.create_check_function(self.regex_patterns["ttc_email"])(value)

    def dlink_check(self, value: str) -> bool:
        """Checks if the given value matches the D-Link port pattern."""
        return self.create_check_function(self.regex_patterns["dlink"])(value)
