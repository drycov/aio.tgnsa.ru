from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    logger.debug("Хеширование пароля")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Проверка пароля")
    return pwd_context.verify(plain_password, hashed_password)
