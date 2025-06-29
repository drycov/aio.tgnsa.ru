from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from app.core.config import settings
from typing import List, Optional, Dict, Any


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
            secret = settings.security.JWT_SECRET
            if secret is None:
                raise ValueError("JWT secret key is not configured")

            payload = jwt.decode(
                token,
                secret.get_secret_value(),
                algorithms=[settings.security.JWT_ALGORITHM],
            )
            return payload
        except ExpiredSignatureError:
            raise ExpiredSignatureError("Token has expired")
        except JWTError as e:
            raise JWTError(f"Token validation failed: {str(e)}")
