# core/services/tfa.py

import pyotp


def verify_tfa_code(secret: str, code: str) -> bool:
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    except Exception:
        return False
