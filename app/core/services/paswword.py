from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["argon2"],  # вместо bcrypt
    deprecated="auto"
)

def hash_password(password: str) -> str:
    logger.debug("Хеширование пароля (argon2)")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Проверка пароля (argon2)")
    return pwd_context.verify(plain_password, hashed_password)

