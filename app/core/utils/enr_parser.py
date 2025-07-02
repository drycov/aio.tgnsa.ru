import requests
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from functools import lru_cache
import time
from app.core.config import logger

# Регистрация Enterprise Number (PEN) - IANA Enterprise Numbers Registry
logger = logger.bind(source="EnterpriseNumberRegistry")


@dataclass
class PENEntry:
    decimal: str
    organization: str
    contact: Optional[str] = None
    email: Optional[str] = None


class EnterpriseNumberRegistry:
    PEN_URL = "https://www.iana.org/assignments/enterprise-numbers.txt"
    CACHE_TTL = 3600  # 1 hour cache
    _last_fetch_time = 0
    _cached_data = None

    @classmethod
    def _fetch_with_cache(cls) -> List[str]:
        """Получает данные с кэшированием по времени."""
        current_time = time.time()
        if (
            current_time - cls._last_fetch_time > cls.CACHE_TTL
            or cls._cached_data is None
        ):
            try:
                response = requests.get(cls.PEN_URL, timeout=10)
                response.raise_for_status()
                cls._cached_data = response.text.splitlines()
                cls._last_fetch_time = current_time
            except requests.RequestException as e:
                logger.error(f"Error fetching PEN data: {e}")
                return []
        return cls._cached_data

    @classmethod
    def _parse_pen_data(cls, data: List[str]) -> List[PENEntry]:
        """Парсит сырые данные PEN в структурированный формат."""
        entries = []
        current_entry = None
        entry_pattern = re.compile(r"^(\d+)\s*$")
        info_pattern = re.compile(r"^\s{4}([^@\n]+)$")
        email_pattern = re.compile(r"^\s{8}([\w.-]+@[\w.-]+)$")

        for line in data:
            if entry_match := entry_pattern.match(line):
                if current_entry:
                    entries.append(current_entry)
                current_entry = PENEntry(decimal=entry_match.group(1), organization="")
            elif info_match := info_pattern.match(line):
                if current_entry:
                    if not current_entry.organization:
                        current_entry.organization = info_match.group(1).strip()
                    elif not current_entry.contact:
                        current_entry.contact = info_match.group(1).strip()
            elif email_match := email_pattern.match(line):
                if current_entry:
                    current_entry.email = email_match.group(1).strip()

        if current_entry:
            entries.append(current_entry)
        return entries

    @classmethod
    @lru_cache(maxsize=128)
    def search_pen(cls, search_term: str) -> List[PENEntry]:
        """
        Ищет в PEN registry по номеру, организации, контакту или email.

        Args:
            search_term: Строка для поиска (регистронезависимая)

        Returns:
            Список совпадающих записей PEN
        """
        raw_data = cls._fetch_with_cache()
        if not raw_data:
            return []

        entries = cls._parse_pen_data(raw_data)
        search_lower = search_term.lower()

        return [
            entry
            for entry in entries
            if (
                search_lower in entry.decimal.lower()
                or search_lower in entry.organization.lower()
                or (entry.contact and search_lower in entry.contact.lower())
                or (entry.email and search_lower in entry.email.lower())
            )
        ]

    @staticmethod
    def parse_oid(oid: str) -> Dict[str, str]:
        """
        Парсит OID на составные части.

        Args:
            oid: Строка OID (например "1.3.6.1.4.1.40418.7.48")

        Returns:
            Словарь с разобранными компонентами OID

        Raises:
            ValueError: Если OID некорректного формата
        """
        if (
            not isinstance(oid, str)
            or not oid
            or any(not part.isdigit() for part in oid.split("."))
        ):
            raise ValueError(
                "Invalid OID format - must contain only digits separated by dots"
            )

        parts = oid.split(".")
        if len(parts) < 7:
            raise ValueError("OID must have at least 7 components")

        return {
            "iso": parts[0],
            "org": parts[1],
            "dod": parts[2],
            "internet": parts[3],
            "private": parts[4],
            "enterprise": parts[5],
            "pen": parts[6],
            "subtree": ".".join(parts[7:]) if len(parts) > 7 else "",
        }


# Пример использования
if __name__ == "__main__":
    # Поиск с кэшированием
    print("Search results for 'cisco':")
    for entry in EnterpriseNumberRegistry.search_pen("cisco"):
        print(f"{entry.decimal}: {entry.organization}")

    # Парсинг OID
    try:
        oid_info = EnterpriseNumberRegistry.parse_oid("1.3.6.1.4.1.9.1.100")
        print("\nParsed OID:", oid_info)
    except ValueError as e:
        print(f"OID Error: {e}")
