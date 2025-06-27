from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings


class JWTManager:
    @staticmethod
    def generate_token(
        subject: str, roles: list[str] = None, expires_sec: int | None = None
    ) -> str:
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
            payload,
            secret.get_secret_value(),
            algorithm=settings.security.JWT_ALGORITHM,
        )
