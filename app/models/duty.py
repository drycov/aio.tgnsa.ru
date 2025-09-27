from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base


class DutyUser(Base):
    """
    Дежурный профиль для User.
    Может содержать отдельные контакты/настройки для онколла.
    """

    __tablename__ = "duty_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Отдельные контакты
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    pager: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Relations ---
    user: Mapped["User"] = relationship("User", back_populates="duty_profile")
    shifts: Mapped[List["DutyShift"]] = relationship(
        "DutyShift", back_populates="duty_user", cascade="all, delete-orphan", lazy="selectin"
    )
    escalations: Mapped[List["DutyEscalation"]] = relationship(
        "DutyEscalation", back_populates="duty_user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DutyUser id={self.id} user_id={self.user_id} active={self.is_active}>"

    @property
    def full_name(self) -> str:
        return self.user.full_name if self.user else "—"


class DutyTeam(Base):
    """
    Команды дежурных (например: NOC, DevOps, Security).
    """

    __tablename__ = "duty_teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Relations ---
    shifts: Mapped[List["DutyShift"]] = relationship(
        "DutyShift", back_populates="team", cascade="all, delete-orphan", lazy="selectin"
    )
    escalations: Mapped[List["DutyEscalation"]] = relationship(
        "DutyEscalation", back_populates="team", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DutyTeam id={self.id} name={self.name}>"


class DutyShift(Base):
    """
    Конкретная смена дежурного в составе команды.
    """

    __tablename__ = "duty_shifts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("duty_teams.id", ondelete="CASCADE"))
    duty_user_id: Mapped[int] = mapped_column(ForeignKey("duty_users.id", ondelete="CASCADE"))

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Relations ---
    team: Mapped["DutyTeam"] = relationship("DutyTeam", back_populates="shifts")
    duty_user: Mapped["DutyUser"] = relationship("DutyUser", back_populates="shifts")

    __table_args__ = (
        UniqueConstraint("team_id", "starts_at", "ends_at", "is_primary", name="uq_team_shift"),
    )

    def __repr__(self) -> str:
        return (
            f"<DutyShift id={self.id} team_id={self.team_id} "
            f"user_id={self.duty_user_id} from={self.starts_at} to={self.ends_at}>"
        )
    def to_human(self) -> str:
        return (
            f"📅 {self.starts_at:%d.%m %H:%M} — {self.ends_at:%d.%m %H:%M} "
            f"({'основное' if self.is_primary else 'резерв'})"
        )

    def is_now_active(self, ts: Optional[datetime] = None) -> bool:
        ts = ts or datetime.utcnow()
        return self.starts_at <= ts < self.ends_at


class DutyEscalation(Base):
    """
    Эскалация: цепочка уведомлений внутри DutyTeam.
    """

    __tablename__ = "duty_escalations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("duty_teams.id", ondelete="CASCADE"), nullable=False)
    duty_user_id: Mapped[int] = mapped_column(ForeignKey("duty_users.id", ondelete="CASCADE"), nullable=False)

    level: Mapped[int] = mapped_column(Integer, nullable=False)  # уровень (0 = primary, 1 = backup)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Relations ---
    team: Mapped["DutyTeam"] = relationship("DutyTeam", back_populates="escalations")
    duty_user: Mapped["DutyUser"] = relationship("DutyUser", back_populates="escalations")

    __table_args__ = (
        UniqueConstraint("team_id", "level", "duty_user_id", name="uq_team_level_user"),
    )

    def __repr__(self) -> str:
        return f"<DutyEscalation team={self.team_id} user={self.duty_user_id} level={self.level}>"
