
import json
import httpx
import re
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from async_lru import alru_cache

from app.core.logging_setup import logger
from app.core.utils.decorators import log_execution
from app.core.config import DATA_DIR
from app.core.context.pen_context import init_search_context, get_search_id, get_search_elapsed

logger = logger.bind(source="EnterpriseNumberRegistry")


@dataclass
class PENEntry:
    decimal: str
    organization: str
    contact: Optional[str] = None
    email: Optional[str] = None


class EnterpriseNumberRegistry:
    PEN_URL = "https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers"
    CACHE_TTL = 3600  # 1 час
    _last_fetch_time = 0
    _cached_data = None
    PEN_CACHE_FILE = DATA_DIR/"pen_cache.json"
    ORG_PATTERN = re.compile(r"^[A-Za-z].*$")  # Для организации
    CONTACT_PATTERN = re.compile(r"^\s{4,}.+")  # Для контакта
    EMAIL_PATTERN = re.compile(r"^\s{6,}\S+@\S+")  # Для email


    @classmethod
    @log_execution(
        level="debug",
        success_message="Данные PEN успешно загружены из IANA.",
        error_message="Ошибка при загрузке данных PEN из IANA",
        log_args=False
    )
    async def _fetch_with_cache_async(cls) -> List[str]:
        search_id = get_search_id()
        logger_ctx = logger.bind(search_id=search_id, phase="fetch")

        current_time = time.time()
        if (
            current_time - cls._last_fetch_time > cls.CACHE_TTL
            or cls._cached_data is None
        ):
            try:
                async with httpx.AsyncClient() as client:
                    start = time.perf_counter()
                    response = await client.get(cls.PEN_URL, timeout=10)
                    response.raise_for_status()
                    cls._cached_data = response.text.splitlines()
                    cls._last_fetch_time = current_time
                    elapsed = time.perf_counter() - start
                    logger_ctx.debug(f"[fetch] Загружено строк: {len(cls._cached_data)} за {elapsed:.2f} сек.")
            except httpx.RequestError as e:
                logger_ctx.error(f"[fetch] Ошибка HTTP-запроса: {e}")
                return []
            except httpx.HTTPStatusError as e:
                logger_ctx.error(f"[fetch] Статус HTTP: {e.response.status_code}")
                return []
        else:
            logger_ctx.debug("[fetch] Использован кэш.")

        return cls._cached_data

    @classmethod
    def _parse_pen_data(cls, data: List[str]) -> List[PENEntry]:
        search_id = get_search_id()
        logger_ctx = logger.bind(search_id=search_id, phase="parse")

        start = time.perf_counter()
        entries = []
        current_entry = None

        for line in data:
            line = line.strip()
            if not line:
                continue

            if re.match(r"^\d+$", line):
                if current_entry:
                    entries.append(current_entry)
                current_entry = PENEntry(decimal=line, organization="", contact=None, email=None)
            elif current_entry is not None:
                if not current_entry.organization and cls.ORG_PATTERN.match(line):
                    current_entry.organization = line
                elif not current_entry.contact and cls.CONTACT_PATTERN.match(line):
                    current_entry.contact = line.strip()
                elif not current_entry.email and cls.EMAIL_PATTERN.match(line):
                    current_entry.email = line.strip()

        if current_entry:
            entries.append(current_entry)

        elapsed = time.perf_counter() - start
        logger_ctx.debug(f"[parse] Обнаружено записей: {len(entries)} за {elapsed:.3f} сек.")
        return [e for e in entries if e.organization]

    @classmethod
    @alru_cache(maxsize=128)
    @log_execution(
        level="info",
        success_message="Поиск по PEN успешно выполнен.",
        error_message="Ошибка поиска в PEN",
        log_args=True
    )
    async def search_pen(cls, search_term: str) -> List[PENEntry]:
        search_id = init_search_context()
        logger_ctx = logger.bind(search_id=search_id, phase="search")

        raw_data = await cls._fetch_with_cache_async()
        if not raw_data:
            logger_ctx.error("[search] Данные не загружены, возвращаю пустой список.")
            return []

        entries = cls._parse_pen_data(raw_data)
        search_lower = search_term.lower()

        matched = [
            entry
            for entry in entries
            if (
                search_lower in entry.decimal.lower()
                or search_lower in entry.organization.lower()
                or (entry.contact and search_lower in entry.contact.lower())
                or (entry.email and search_lower in entry.email.lower())
            )
        ]

        logger_ctx.info(f"[search] Найдено совпадений: {len(matched)} по запросу '{search_term}'")
        for e in matched:
            logger_ctx.debug(f"[search] Найдено: {e.decimal} — {e.organization}")

        total_time = get_search_elapsed()
        logger_ctx.info(f"[search] Выполнено за {total_time:.3f} сек.")

        return matched

    @classmethod
    @alru_cache(maxsize=1024)
    async def search_pen_cached(cls, search_term: str) -> List[PENEntry]:
        return await cls.search_pen(search_term)

    @staticmethod
    @log_execution(
        level="debug",
        success_message="OID успешно разобран.",
        error_message="Ошибка разбора OID",
        log_args=True
    )
    def parse_oid(oid: str) -> Dict[str, str]:
        if (
            not isinstance(oid, str)
            or not oid
            or any(not part.isdigit() for part in oid.split("."))
        ):
            raise ValueError("Invalid OID format - must contain only digits separated by dots")

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

