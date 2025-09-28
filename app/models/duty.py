# app/models/duty.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.models.user import User


# ==============================
# DutyUser
# ==============================
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
    user: Mapped[User] = relationship(back_populates="duty_profile")
    team_members: Mapped[List["DutyTeamMember"]] = relationship(
        back_populates="duty_user", cascade="all, delete-orphan", lazy="selectin"
    )
    shifts: Mapped[List["DutyShift"]] = relationship(
        back_populates="duty_user", cascade="all, delete-orphan", lazy="selectin"
    )
    escalations: Mapped[List["DutyEscalation"]] = relationship(
        back_populates="duty_user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DutyUser id={self.id} user_id={self.user_id} active={self.is_active}>"

    @property
    def full_name(self) -> str:
        return getattr(self.user, "full_name", "—")


# ==============================
# DutyTeam
# ==============================
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

    members: Mapped[List["DutyTeamMember"]] = relationship(
        back_populates="team", cascade="all, delete-orphan", lazy="selectin"
    )
    shifts: Mapped[List["DutyShift"]] = relationship(
        back_populates="team", cascade="all, delete-orphan", lazy="selectin"
    )
    escalations: Mapped[List["DutyEscalation"]] = relationship(
        back_populates="team", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DutyTeam id={self.id} name={self.name}>"


# ==============================
# DutyTeamMember (M2M)
# ==============================
class DutyTeamMember(Base):
    """
    Связка DutyUser ↔ DutyTeam с ролью (member, lead и т.д.)
    """

    __tablename__ = "duty_team_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("duty_teams.id", ondelete="CASCADE"))
    duty_user_id: Mapped[int] = mapped_column(ForeignKey("duty_users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    team: Mapped["DutyTeam"] = relationship(back_populates="members")
    duty_user: Mapped["DutyUser"] = relationship(back_populates="team_members")

    __table_args__ = (
        UniqueConstraint("team_id", "duty_user_id", name="uq_member_team_user"),
    )

    def __repr__(self) -> str:
        return f"<DutyTeamMember team={self.team_id} user={self.duty_user_id} role={self.role}>"


# ==============================
# DutyShift
# ==============================
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

    role: Mapped[str] = mapped_column(String(20), default="primary", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    team: Mapped["DutyTeam"] = relationship(back_populates="shifts")
    duty_user: Mapped["DutyUser"] = relationship(back_populates="shifts")

    __table_args__ = (
        UniqueConstraint("team_id", "starts_at", "ends_at", "role", name="uq_team_shift"),
        Index("idx_shift_team_start", "team_id", "starts_at"),
        CheckConstraint("starts_at < ends_at", name="ck_shift_time_valid"),
    )

    def __repr__(self) -> str:
        return (
            f"<DutyShift id={self.id} team_id={self.team_id} "
            f"user_id={self.duty_user_id} from={self.starts_at} to={self.ends_at} role={self.role}>"
        )

    def to_human(self) -> str:
        return f"📅 {self.starts_at:%d.%m %H:%M} — {self.ends_at:%d.%m %H:%M} ({self.role})"

    def is_now_active(self, ts: Optional[datetime] = None) -> bool:
        ts = ts or datetime.now(timezone.utc)
        return self.starts_at <= ts < self.ends_at


# ==============================
# DutyEscalation
# ==============================
class DutyEscalation(Base):
    """
    Эскалация: цепочка уведомлений внутри DutyTeam.
    """

    __tablename__ = "duty_escalations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("duty_teams.id", ondelete="CASCADE"), nullable=False)
    duty_user_id: Mapped[int] = mapped_column(ForeignKey("duty_users.id", ondelete="CASCADE"), nullable=False)

    level: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    team: Mapped["DutyTeam"] = relationship(back_populates="escalations")
    duty_user: Mapped["DutyUser"] = relationship(back_populates="escalations")

    __table_args__ = (
        UniqueConstraint("team_id", "level", "duty_user_id", name="uq_team_level_user"),
        Index("idx_escalation_team_level", "team_id", "level"),
    )

    def __repr__(self) -> str:
        return (
            f"<DutyEscalation team={self.team_id} user={self.duty_user_id} "
            f"level={self.level} order={self.order_index} enabled={self.is_enabled}>"
        )


# ==============================
# DutySwapRequest
# ==============================
class DutySwapRequest(Base):
    __tablename__ = "duty_swap_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("duty_users.id", ondelete="CASCADE"))
    shift_id: Mapped[int] = mapped_column(ForeignKey("duty_shifts.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / confirmed / cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    duty_user: Mapped["DutyUser"] = relationship("DutyUser")
    shift: Mapped["DutyShift"] = relationship("DutyShift")

    def __repr__(self) -> str:
        return f"<DutySwapRequest id={self.id} shift={self.shift_id} from={self.from_user_id} status={self.status}>"
