# core/services/tfa.py
import logging
import pyotp

logger = logging.getLogger(__name__)


def generate_tfa_secret() -> str:
    """
    Генерация нового секрета для TFA (Base32).
    Обычно сохраняется в БД у пользователя.
    """
    secret = pyotp.random_base32()
    logger.debug("Сгенерирован новый TFA секрет")
    return secret


def get_totp_uri(secret: str, username: str, issuer: str = "TG NMS") -> str:
    """
    Генерация otpauth:// URI для Google Authenticator.
    Можно использовать для генерации QR-кода.
    """
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name=issuer)
    logger.debug("Сформирован otpauth URI для пользователя %s", username)
    return uri


def verify_tfa_code(secret: str, code: str) -> bool:
    """
    Проверка TFA-кода (6 цифр).
    """
    try:
        totp = pyotp.TOTP(secret)
        result = totp.verify(code, valid_window=1)  # valid_window=1 → допускаем ±30 сек
        logger.debug("Результат проверки TFA-кода: %s", result)
        return result
    except Exception as e:
        logger.error("Ошибка при проверке TFA-кода: %s", e)
        return False
