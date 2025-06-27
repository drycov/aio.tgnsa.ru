from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings


class JWTManager:
    """
    Утилита для работы с JWT-токенами (генерация, валидация).

    Использует библиотеку python‑jose для подписи HS256/RS256 токенов.
    """

    @staticmethod
    def generate_token(
        subject: str, roles: list[str] | None = None, expires_sec: int | None = None
    ) -> str:
        """
        Генерирует подписанный JWT‑токен.

        :param subject: Идентификатор субъекта (обычно user_id)
        :param roles: Список ролей или прав доступа
        :param expires_sec: Время жизни токена в секундах.
                             По умолчанию – из настроек безопасности.
        :return: Строка JWT

        :raises ValueError: если секрет не настроен

        Пример:
        ```python
        token = JWTManager.generate_token(
            subject="user123",
            roles=["admin", "editor"],
            expires_sec=3600
        )
        ```
        """
        secret = settings.security.JWT_SECRET
        if secret is None:
            raise ValueError("JWT secret key is not configured")

        now = datetime.utcnow()
        expire = now + timedelta(
            seconds=expires_sec or settings.security.ACCESS_TOKEN_EXPIRE_SECONDS
        )
        payload = {
            "sub": subject,
            "iat": now,
            "exp": expire,
            "roles": roles or [],
        }

        return jwt.encode(
            payload=payload,
            key=secret.get_secret_value(),
            algorithm=settings.security.JWT_ALGORITHM,
        )

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Декодирует и валидирует JWT, возвращает полезную нагрузку.

        :param token: строка JWT
        :return: словарь payload
        :raises jwt.ExpiredSignatureError: если срок истёк
        :raises jwt.JWTError: при других ошибках валидации
        """
        return jwt.decode(
            token,
            settings.security.JWT_SECRET.get_secret_value(),
            algorithms=[settings.security.JWT_ALGORITHM],
        )
