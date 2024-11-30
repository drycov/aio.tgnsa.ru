import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from jose import jwt, JWTError


class JWTManager:

    @staticmethod
    def generate_jwt(user_id: int, secret_key: str, expires_in: str = '1h', uid: str = str(uuid.uuid4())
                     ) -> str:
        """
        Генерирует JWT токен с информацией о пользователе.
        :param user_id: Идентификатор пользователя (tg_id).
        :param secret_key: Секретный ключ для подписи токена.
        :param expires_in: Время жизни токена в минутах (по умолчанию 60 минут).
        :return: Строка JWT токена.
        """
        from bot.utils import HelperFunctions

        try:
            expiration_minutes = HelperFunctions.parse_expiration_time(expires_in)
            expiration = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)

            payload = {
                "uid": uid,  # Включаем UUID в токен
                'user_id': user_id,
                'exp': expiration,
                'iat': datetime.now(timezone.utc)
            }
            return jwt.encode(payload, secret_key, algorithm='HS256')
        except Exception as e:
            raise ValueError(f"Ошибка при генерации JWT токена: {e}")

    @staticmethod
    def decode_jwt(token: str, secret_key: str) -> Optional[dict]:
        """
        Декодирует JWT токен и возвращает данные пользователя, если токен валиден.
        :param token: JWT токен.
        :param secret_key: Секретный ключ для проверки подписи токена.
        :return: Словарь с данными пользователя или None, если токен недействителен.
        """
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except JWTError as e:
            if "Signature has expired" in str(e):
                print("JWT токен просрочен.")
            else:
                print("Неверный JWT токен.")
            return None
