from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


class JWTManager:
    """
    Utility for working with JWT tokens (generation, validation).

    Uses the python-jose library for signing HS256/RS256 tokens.
    """

    @staticmethod
    def generate_token(
        subject: str,
        roles: Optional[List[str]] = None,
        expires_sec: Optional[int] = None,
    ) -> str:
        """
        Generates a signed JWT token.

        :param subject: Identifier of the subject (usually user_id)
        :param roles: List of roles or access rights
        :param expires_sec: Token lifetime in seconds.
                            Default is from security settings.
        :return: JWT string

        :raises ValueError: if the secret key is not configured

        Example:
        ```python
        token = JWTManager.generate_token(
            subject="user123",
            roles=["admin", "editor"],
            expires_sec=3600
        )
        ```
        """
        secret = settings.security.jwt_secret
        if secret is None:
            raise ValueError("JWT secret key is not configured")

        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            seconds=expires_sec or settings.security.access_token_expire_minutes
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
            algorithm=settings.security.jwt_algorithm,
        )

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decodes and validates a JWT, returning the payload.

        :param token: JWT string
        :return: Payload dictionary
        :raises ExpiredSignatureError: if the token has expired
        :raises JWTError: for other validation errors
        """
        try:
            secret = settings.security.jwt_secret
            if secret is None:
                raise ValueError("JWT secret key is not configured")

            payload = jwt.decode(
                token,
                secret.get_secret_value(),
                algorithms=[settings.security.jwt_algorithm],
            )
            return payload
        except ExpiredSignatureError:
            raise ExpiredSignatureError("Token has expired")
        except JWTError as e:
            raise JWTError(f"Token validation failed: {str(e)}")
