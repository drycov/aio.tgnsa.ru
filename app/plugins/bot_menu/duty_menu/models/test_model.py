# app/models/test_model.py
from sqlalchemy.orm import Mapped, mapped_column
from app.core.base import Base


class TestModel(Base):
    """
    Простейшая тестовая модель для проверки автозагрузки моделей.
    """
    __tablename__ = "test_model"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[int] = mapped_column(default=0)
