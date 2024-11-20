"""
This module configures the bot, sets up handlers, and manages lifecycle operations.
"""

from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from app import handlers
from app.bot_instance import dp, bot
from app.constants import Messages
from app.middlewares import (
    CustomLoggingMiddleware,
    RateLimitMiddleware,
    UserActivityMiddleware,
    AuthMiddleware,
)
from app.utils.logger_instance import app_logger
from config import Config

dp.update.middleware(RateLimitMiddleware())
dp.update.middleware(UserActivityMiddleware())
dp.update.middleware(AuthMiddleware())


def setup_bot():
    """
    Настройка бота и регистрация обработчиков.
    """
    app_logger.info(Messages.START_BOT_SETUP.value)
    router = handlers.get_handlers_router()
    app_logger.info(Messages.REGISTER_HANDLERS.value)
    dp.include_router(router)
    dp.update.middleware(CallbackAnswerMiddleware())
    dp.update.middleware(AuthMiddleware())

    Config.DEBUG = True
    if Config.DEBUG:
        dp.update.middleware(CustomLoggingMiddleware())
    app_logger.info(Messages.BOT_SETUP_COMPLETE.value)


async def start_bot(on_startup=None):
    """
    Запускает бота и начинает обработку сообщений.
    """
    if on_startup:
        await on_startup()
    setup_bot()
    app_logger.info(Messages.DELETE_WEBHOOK.value)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
        on_shutdown=graceful_shutdown,
    )
    app_logger.info(Messages.START_BOT.value)


async def graceful_shutdown():
    """
    Функция для корректного завершения работы бота и всех подключений.
    """
    app_logger.info("Начато корректное завершение работы бота...")

    # Остановка Health API сервера, если он запущен
    # pylint: disable=import-outside-toplevel
    from admin import stop_server
    stop_server()

    # Закрытие FSM-хранилища
    await dp.storage.close()
    app_logger.info("Хранилище FSM закрыто.")

    # Закрытие HTTP-сессии бота
    await bot.session.close()
    app_logger.info("HTTP-сессия бота закрыта.")

    app_logger.info("Работа бота завершена.")
