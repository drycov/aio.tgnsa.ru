
from passlib.context import CryptContext

from app.core.config import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    logger.debug("Хеширование пароля")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Проверка пароля")
    return pwd_context.verify(plain_password, hashed_password)
