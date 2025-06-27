from __future__ import annotations
from datetime import timedelta

from datetime import datetime
from typing import List, Optional
from app.core.config import settings
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from jose import jwt
from app.core.jwt_manager import JWTManager
from app.core.base import Base
from app.models.role import Role  # ← Убедись, что импорт есть


# Ассоциативная таблица User ↔ Role (many-to-many)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_post: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_phone_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    banned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    roles: Mapped[List[Role]] = relationship(
        back_populates="users",
        secondary=user_roles,
        lazy="joined",
    )

    @property
    def full_name(self) -> str:
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.username or ""

    def is_admin(self) -> bool:
        return any(role.name == "admin" for role in self.roles)

    def generate_jwt(self) -> str:
        return JWTManager.generate_token(
            subject=str(self.tg_id),
            roles=[role.name for role in self.roles],
        )
