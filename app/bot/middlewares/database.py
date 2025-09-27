from typing import Any, Awaitable, Callable, Dict
from contextlib import asynccontextmanager

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DBAPIError

from app.core.utils.logger_manager import LoggerManager


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для управления асинхронными сессиями SQLAlchemy.

    Особенности:
    - Автоматическое управление транзакциями (commit/rollback)
    - Повторы при временных ошибках
    - Подробное логирование операций
    - Поддержка вложенных транзакций
    - Режим readonly (без коммита)
    """

    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        logger: LoggerManager,
        auto_commit: bool = True,
        auto_rollback: bool = True,
        log_sql: bool = False,
        max_retries: int = 0,
        readonly: bool = False,
    ):
        self.sessionmaker = sessionmaker
        self.logger = logger
        self.auto_commit = auto_commit and not readonly
        self.auto_rollback = auto_rollback
        self.log_sql = log_sql
        self.max_retries = max_retries
        self.readonly = readonly

    @asynccontextmanager
    async def _session_scope(self):
        """Контекстный менеджер для управления сессией."""
        session = self.sessionmaker()
        if self.log_sql and session.bind:
            session.bind.echo = True

        try:
            self.logger.debug("🚀 Открытие новой сессии БД")
            yield session

            if self.auto_commit:
                await session.commit()
                self.logger.debug("✅ Транзакция зафиксирована")
        except (IntegrityError, OperationalError, DBAPIError) as e:
            if self.auto_rollback:
                self.logger.warning(f"⚠️ Ошибка транзакции ({type(e).__name__}), rollback")
                await session.rollback()
            raise
        except SQLAlchemyError as e:
            if self.auto_rollback:
                self.logger.error(f"❌ SQLAlchemy ошибка: {e}, rollback")
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
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                async with self._session_scope() as session:
                    data["db"] = session
                    data["db_session"] = session
                    return await handler(event, data)

            except (OperationalError, DBAPIError) as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    self.logger.exception(
                        f"🔥 Превышен лимит повторов ({self.max_retries}) из-за ошибки: {e}"
                    )
                    raise

                self.logger.warning(
                    f"🔄 Попытка {retry_count}/{self.max_retries} после OperationalError: {e}"
                )
                continue

            except Exception as e:
                self.logger.exception(f"⚠️ Неожиданная ошибка в обработчике: {e}")
                raise


class OptionalDatabaseMiddleware(DatabaseMiddleware):
    """
    Вариант DatabaseMiddleware, который использует существующую сессию,
    если она уже есть в data.
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
