from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from bot import handlers
from bot.constants import Messages
from bot.middlewares import (
    CustomLoggingMiddleware,
    RateLimitMiddleware,
    UserActivityMiddleware,
    AuthMiddleware,
)
from bot.utils.logger_instance import app_logger
from config import Config


class BotManager:
    """
    Класс для управления настройкой, запуском и остановкой Telegram бота.
    """

    def __init__(self, token: str):
        from .bot_instance import bot, dp
        """
        Инициализация бота и диспетчера.
        """
        self.bot = bot
        self.dp = dp
        self._is_setup = False

    def setup_bot(self):
        """
        Настройка бота и регистрация обработчиков.
        """
        if self._is_setup:
            app_logger.warning("Бот уже настроен. Повторная настройка пропущена.")
            return

        app_logger.info(Messages.START_BOT_SETUP.value)

        # Подключение обработчиков
        router = handlers.get_handlers_router()
        self.dp.include_router(router)

        # Подключение middlewares
        self.dp.update.middleware(RateLimitMiddleware())
        self.dp.update.middleware(UserActivityMiddleware())
        self.dp.update.middleware(AuthMiddleware())
        self.dp.update.middleware(CallbackAnswerMiddleware())

        if Config.DEBUG:
            self.dp.update.middleware(CustomLoggingMiddleware())

        self._is_setup = True
        app_logger.info(Messages.BOT_SETUP_COMPLETE.value)

    async def start_bot(self):
        """
        Запускает бота и начинает обработку сообщений.
        """
        app_logger.info(Messages.START_BOT.value)

        # Убедимся, что бот настроен перед запуском
        self.setup_bot()

        # Удаление старого вебхука
        app_logger.info(Messages.DELETE_WEBHOOK.value)
        await self.bot.delete_webhook(drop_pending_updates=True)

        # Запуск polling
        try:
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types(),
                on_shutdown=self.graceful_shutdown,
            )
        except Exception as e:
            app_logger.error(f"Ошибка во время запуска бота: {e}")

    async def shutdown_bot(self):
        """
        Останавливает процессы, связанные с ботом.
        """
        try:
            # Остановка polling
            await self.dp.stop_polling()
            app_logger.info("Диспетчер успешно остановлен.")

            # Закрытие HTTP-сессии
            await self.bot.session.close()
            app_logger.info("HTTP-сессия успешно закрыта.")
        except Exception as e:
            app_logger.error(f"Ошибка при остановке бота: {e}")

    async def restart_bot(self):
        """
        Перезапуск бота.
        """
        try:
            await self.shutdown_bot()
            await self.start_bot()
            app_logger.info("Бот успешно перезапущен.")
        except Exception as e:
            app_logger.error(f"Ошибка при перезапуске бота: {e}")
            raise

    async def graceful_shutdown(self):
        """
        Корректное завершение работы бота.
        """
        app_logger.info("Начато корректное завершение работы бота...")

        # Закрытие FSM-хранилища
        await self.dp.storage.close()
        app_logger.info("Хранилище FSM закрыто.")

        # Закрытие HTTP-сессии
        await self.bot.session.close()
        app_logger.info("HTTP-сессия закрыта.")

        app_logger.info("Работа бота завершена.")


# Инициализация глобального экземпляра BotManager
bot_manager = BotManager(token=Config.API_TOKEN)
