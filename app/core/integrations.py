# app/core/integrations.py
from app.core.config import settings
from app.integrations.phpipam import PhpIpamAsyncClient
from app.core.logging_setup import logger

# Инициализация клиента phpIPAM
phpipam_client = PhpIpamAsyncClient(
    base_url=settings.phpipam.url,
    app_id=settings.phpipam.app_id,
    username=settings.phpipam.user,
    password=settings.phpipam.password,
    verify_ssl=settings.phpipam.verify_ssl,
)


def register_integrations(lifecycle):
    """Регистрация внешних интеграций (phpIPAM в безопасном режиме)."""

    async def safe_start():
        try:
            await phpipam_client.startup()
            if phpipam_client.is_alive():
                logger.info("🔌 PhpIPAM client is alive and ready")
            else:
                logger.warning("⚠️ PhpIPAM client initialized, но не активен")
        except Exception as e:
            # помечаем клиент как нерабочий
            await phpipam_client._mark_dead()

    async def safe_stop():
        try:
            await phpipam_client.shutdown()
            logger.info("🔌 PhpIPAM shutdown completed")
        except Exception as e:
            logger.warning("⚠️ PhpIPAM shutdown failed: %s", e)

    # Регистрируем хуки
    lifecycle.on_startup()(safe_start)
    lifecycle.on_shutdown()(safe_stop)

    logger.info("🔧 PhpIPAM integration registered (safe mode)")
