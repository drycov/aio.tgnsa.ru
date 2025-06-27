from __future__ import annotations

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base


class Role(Base):
    __tablename__ = "roles"
    from .user import User

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    @staticmethod
    def default_roles():
        return ["admin", "user", "candidat"]

    users: Mapped[List["User"]] = relationship(  # type: ignore
        "User",
        back_populates="roles",
        # Название таблицы many-to-many (указано явно, допустимо)
        secondary="user_roles",
        # Оптимально для большинства use-case (можно noload/joined по необходимости)
        lazy="selectin",
    )
