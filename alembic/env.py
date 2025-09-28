from logging.config import fileConfig
import logging

from sqlalchemy import create_engine, pool
from alembic import context

from app.core.base import Base
from app.core.config import settings
from app.models import *  # Обязательно: импорт всех моделей для Alembic

# Конфигурация Alembic из alembic.ini
config = context.config

# Настройка логгирования, если указано в alembic.ini
if config.config_file_name:
    fileConfig(config.config_file_name)

# Метаданные моделей для автогенерации миграций
target_metadata = Base.metadata

def process_revision_directives(context, revision, directives):
    if context.config.cmd_opts.autogenerate:
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] = []
            print('No changes in schema detected.')


def get_url() -> str:
    """Получить DSN синхронной БД"""
    return settings.db.get_sync_dsn()

logger = logging.getLogger("alembic.env")
logger.info(f"Using database URL: {get_url()}")

def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (без подключения к БД)"""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций в online-режиме (с реальным подключением к БД)"""
    connectable = create_engine(
        get_url(),
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


# Определение режима запуска
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
