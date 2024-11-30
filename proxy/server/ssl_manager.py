from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta, timezone
from pathlib import Path
from proxy.config import CERT_FILE, KEY_FILE, logger


def generate_ssl_certificates():
    """
    Создаёт самоподписанный SSL-сертификат, если его нет.
    """
    if not CERT_FILE.exists() or not KEY_FILE.exists():
        logger.info("Сертификаты не найдены. Генерация новых сертификатов...")
        try:
            # Создаём приватный ключ
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            public_key = private_key.public_key()

            # Определяем параметры сертификата
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Organization"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            current_time = datetime.now(timezone.utc)

            # Создаём самоподписанный сертификат
            certificate = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(public_key)
                .serial_number(x509.random_serial_number())
                .not_valid_before(current_time)
                .not_valid_after(current_time + timedelta(days=365))
                .add_extension(
                    x509.BasicConstraints(ca=True, path_length=None), critical=True
                )
                .sign(private_key, hashes.SHA256())
            )

            # Сохраняем сертификат
            with open(CERT_FILE, "wb") as cert_file:
                cert_file.write(certificate.public_bytes(Encoding.PEM))

            # Сохраняем приватный ключ
            with open(KEY_FILE, "wb") as key_file:
                key_file.write(
                    private_key.private_bytes(
                        encoding=Encoding.PEM,
                        format=PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=NoEncryption(),
                    )
                )

            logger.info("Сертификаты успешно созданы.")
        except Exception as e:
            logger.error(f"Ошибка при создании сертификатов: {e}")
            raise RuntimeError("Не удалось создать SSL-сертификаты.")
    else:
        logger.info("Сертификаты уже существуют. Генерация не требуется.")


def validate_ssl_certificates():
    """
    Проверяет существование сертификатов и их валидность.
    """
    if not CERT_FILE.exists() or not KEY_FILE.exists():
        logger.warning("Сертификаты отсутствуют.")
        return False

    try:
        with open(CERT_FILE, "rb") as cert_file:
            cert = x509.load_pem_x509_certificate(cert_file.read())
            # Используем not_valid_after_utc для получения времени истечения сертификата
            if cert.not_valid_after_utc < datetime.now(timezone.utc):
                logger.warning("Срок действия сертификата истёк.")
                return False
    except Exception as e:
        logger.error(f"Ошибка проверки сертификата: {e}")
        return False

    logger.info("Сертификаты валидны.")
    return True
