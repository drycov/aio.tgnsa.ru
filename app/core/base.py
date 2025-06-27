from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Базовый класс для декларативного определения ORM‑моделей в SQLAlchemy 2.x.

    Наследование от этого класса позволяет автоматически применять declarative mapping
    ко всем подклассам:

        class User(Base):
            __tablename__ = "user"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

    Обновлённый стиль (с использованием DeclarativeBase) заменяет устаревшую функцию
    `declarative_base()` и тесно интегрируется с механизмом типизации PEP 484. Кроме того,
    поддерживает указание собственного registry:

        from sqlalchemy.orm import registry

        reg = registry()
        class BaseWithCustomRegistry(DeclarativeBase):
            registry = reg

    Он автоматически создаёт MetaData в `Base.metadata` и использует
    mapper<->table конфигурацию за кулисами. Рекомендуется к применению как
    стандартный способ объявления ORM‑моделей с v2.0.
    """

    pass
