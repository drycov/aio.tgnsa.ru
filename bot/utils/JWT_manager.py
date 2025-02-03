import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from jose import jwt, JWTError, ExpiredSignatureError



class JWTManager:

    @staticmethod
    def generate_jwt(
        user_id: int,
        secret_key: str,
        expires_in: str = '1h',
        uid: Optional[str] = None
    ) -> str:
        """
        Генерирует JWT токен с информацией о пользователе.
        :param user_id: Идентификатор пользователя (tg_id)
        :param secret_key: Секретный ключ для подписи токена
        :param expires_in: Время жизни токена в формате времени (например: '1h', '30m')
        :param uid: Уникальный идентификатор токена (по умолчанию генерируется новый UUID4)
        :return: Строка JWT токена
        """
        from bot.utils import HelperFunctions  # Импорт вынесен на уровень модуля
        try:
            expiration_minutes = HelperFunctions.parse_expiration_time(expires_in)
            expiration = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
            
            payload = {
                "uid": uid or str(uuid.uuid4()),
                "user_id": user_id,
                "exp": expiration,
                "iat": datetime.now(timezone.utc)
            }
            return jwt.encode(payload, secret_key, algorithm="HS256")
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid expiration time format: {e}")
        except Exception as e:
            raise RuntimeError(f"JWT generation failed: {e}") from e

    @staticmethod
    def decode_jwt(token: str, secret_key: str) -> Optional[dict]:
        """
        Декодирует JWT токен и возвращает данные пользователя, если токен валиден
        :param token: JWT токен
        :param secret_key: Секретный ключ для проверки подписи токена
        :return: Словарь с данными пользователя или None, если токен недействителен
        """
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except ExpiredSignatureError:
            print("JWT token expired")
        except JWTError:
            print("Invalid JWT token")
        return None