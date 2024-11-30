import secrets
from datetime import datetime, timezone

from proxy.core import list_users
from proxy.config import logger


def generate_token():
    """Генерация уникального токена."""
    return secrets.token_hex(16)


def validate_authorization_header(auth_header):
    """Проверка корректности заголовка авторизации."""
    if not auth_header:
        logger.warning("Заголовок авторизации отсутствует.")
        return None
    if not auth_header.startswith("Bearer "):
        logger.warning("Некорректный формат заголовка авторизации.")
        return None
    return auth_header.split(" ", 1)[1]


async def fetch_valid_tokens():
    """Асинхронный генератор для получения валидных токенов."""
    users = await list_users()
    current_time = datetime.now(timezone.utc)

    logger.info(f"Найдено {len(users)} пользователей.")

    for user in users:
        expiry_date_raw = user[2]
        if not isinstance(expiry_date_raw, str):
            try:
                expiry_date_raw = expiry_date_raw.isoformat()  # Преобразование даты в строку ISO 8601
            except AttributeError:
                logger.warning(f"Неверный формат даты для пользователя {user[0]}: {expiry_date_raw}")
                continue

        try:
            expiry_date = datetime.fromisoformat(expiry_date_raw).replace(tzinfo=timezone.utc)
            if expiry_date > current_time:
                yield user[1], expiry_date  # (токен, срок действия)
        except ValueError as e:
            logger.error(f"Ошибка преобразования даты для пользователя {user[0]}: {e}")


async def is_authorized(headers):
    """Проверка авторизации пользователя."""
    auth_header = headers.get("X-VPN-Auth")
    if not auth_header:
        logger.warning("Заголовок авторизации отсутствует.")
        return False

    # auth_header = headers.get("Authorization")
    token = validate_authorization_header(auth_header)
    if not token:
        return False

    async for valid_token, expiry_date in fetch_valid_tokens():
        if token == valid_token:
            logger.info(f"Авторизация успешна для токена: {token[:4]}...{token[-4:]}")
            return True

    logger.warning(f"Авторизация не удалась для токена: {token[:4]}...{token[-4:]}")
    return False
