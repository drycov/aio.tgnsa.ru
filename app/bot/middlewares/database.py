from typing import Any, Awaitable, Callable, Dict
from contextlib import asynccontextmanager

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.core.utils.logger_manager import LoggerManager


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для управления асинхронными сессиями SQLAlchemy.

    Особенности:
    - Автоматическое управление транзакциями (commit/rollback)
    - Гибкая настройка поведения при ошибках
    - Подробное логирование операций
    - Поддержка вложенных транзакций
    - Возможность отключения автоматического управления транзакциями
    """

    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        logger: LoggerManager,
        auto_commit: bool = True,
        auto_rollback: bool = True,
        log_sql: bool = False,
        max_retries: int = 0,
    ):
        """
        Инициализация middleware.

        Args:
            sessionmaker: Фабрика асинхронных сессий SQLAlchemy
            logger: Логгер для записи событий
            auto_commit: Автоматически коммитить при успешном выполнении
            auto_rollback: Автоматически откатывать при ошибках
            log_sql: Логировать SQL-запросы (требуется настройка в SQLAlchemy)
            max_retries: Максимальное количество попыток повтора при ошибках
        """
        self.sessionmaker = sessionmaker
        self.logger = logger
        self.auto_commit = auto_commit
        self.auto_rollback = auto_rollback
        self.log_sql = log_sql
        self.max_retries = max_retries

    @asynccontextmanager
    async def _session_scope(self):
        """Контекстный менеджер для управления сессией."""
        session = self.sessionmaker()
        if self.log_sql:
            session.bind.echo = True

        try:
            self.logger.debug("🚀 Открытие новой сессии БД")
            yield session

            if self.auto_commit:
                await session.commit()
                self.logger.debug("🔄 Коммит транзакции выполнен")
        except SQLAlchemyError as e:
            if self.auto_rollback:
                self.logger.error(f"❌ Ошибка БД, выполнение rollback: {str(e)}")
                await session.rollback()
            raise
        finally:
            await session.close()
            self.logger.debug("🏁 Сессия БД закрыта")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обработка запроса с управлением сессией БД.

        Args:
            handler: Обработчик запроса
            event: Объект события (сообщение, callback и т.д.)
            data: Контекстные данные

        Returns:
            Результат выполнения обработчика

        Raises:
            Exception: Любые ошибки, возникшие при обработке запроса
        """
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                async with self._session_scope() as session:
                    # Добавляем сессию в контекст обработчика
                    data["db"] = session
                    data["db_session"] = session

                    result = await handler(event, data)
                    return result

            except SQLAlchemyError as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    self.logger.exception(
                        f"🔥 Превышено максимальное количество попыток ({self.max_retries})"
                    )
                    raise

                self.logger.warning(
                    f"🔄 Повторная попытка ({retry_count}/{self.max_retries}) после ошибки БД: {str(e)}"
                )

            except Exception as e:
                self.logger.exception(f"⚠️ Неожиданная ошибка в обработчике: {str(e)}")
                raise


class OptionalDatabaseMiddleware(DatabaseMiddleware):
    """
    Расширение DatabaseMiddleware с поддержкой опционального использования БД.
    Если сессия уже существует в данных, новая не создается.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if "db" in data and isinstance(data["db"], AsyncSession):
            self.logger.debug("♻️ Использование существующей сессии БД")
            return await handler(event, data)

        return await super().__call__(handler, event, data)
