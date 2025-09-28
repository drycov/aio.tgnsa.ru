from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.duty import (
    DutyEscalation,
    DutySwapRequest,
    DutyUser,
    DutyShift,
    DutyTeam,
    DutyTeamMember,
)

# === Константы ===
PERIOD_DAY = "day"
PERIOD_WEEK = "week"
PERIOD_MONTH = "month"
PERIOD_ALL = "all"


# === Утилиты ===
def _get_period_range(now: date, period: str) -> Tuple[datetime, datetime]:
    """Возвращает (start, end) для фильтрации смен по периоду."""
    if period == PERIOD_DAY:
        return (
            datetime.combine(now, datetime.min.time()),
            datetime.combine(now, datetime.max.time()),
        )
    elif period == PERIOD_WEEK:
        start = datetime.combine(now, datetime.min.time()) - timedelta(days=now.weekday())
        end = start + timedelta(days=7)  # [start, end)
        return start, end
    elif period == PERIOD_MONTH:
        start = datetime(now.year, now.month, 1)
        end = datetime(now.year + (now.month // 12), ((now.month % 12) + 1), 1)
        return start, end
    else:
        # без фильтра
        return datetime.min, datetime.max


def _period_filter(period: str, base: Optional[date] = None):
    """Фильтр по периоду относительно base (по умолчанию сегодня). Возвращает SA-выражение или None."""
    base = base or date.today()

    if period == PERIOD_WEEK:
        start = datetime.combine(base - timedelta(days=base.weekday()), datetime.min.time())
        end = start + timedelta(days=7)
        return and_(DutyShift.starts_at >= start, DutyShift.starts_at < end)

    elif period == PERIOD_MONTH:
        start = datetime(base.year, base.month, 1)
        end = datetime(base.year + (base.month // 12), ((base.month % 12) + 1), 1)
        return and_(DutyShift.starts_at >= start, DutyShift.starts_at < end)

    elif period == PERIOD_DAY:
        start = datetime.combine(base, datetime.min.time())
        end = datetime.combine(base, datetime.max.time())
        return and_(DutyShift.starts_at >= start, DutyShift.starts_at <= end)

    return None


# === Профиль ===
async def ensure_duty_profile(session: AsyncSession, user: User) -> DutyUser:
    """
    Проверяет, что у пользователя есть DutyUser и членство в команде (по department).
    Если чего-то не хватает — создаёт автоматически.
    """
    duty_user = (
        await session.execute(select(DutyUser).where(DutyUser.user_id == user.id))
    ).scalar_one_or_none()

    if not duty_user:
        duty_user = DutyUser(user_id=user.id, is_active=True)
        session.add(duty_user)
        await session.flush()

    dept_name = user.department or "General"
    team = (
        await session.execute(select(DutyTeam).where(DutyTeam.name == dept_name))
    ).scalar_one_or_none()

    if not team:
        team = DutyTeam(name=dept_name, description=f"Команда подразделения {dept_name}")
        session.add(team)
        await session.flush()

    member = (
        await session.execute(
            select(DutyTeamMember).where(
                DutyTeamMember.team_id == team.id,
                DutyTeamMember.duty_user_id == duty_user.id,
            )
        )
    ).scalar_one_or_none()

    if not member:
        session.add(DutyTeamMember(team_id=team.id, duty_user_id=duty_user.id, role="member"))

    escalation = (
        await session.execute(
            select(DutyEscalation).where(
                DutyEscalation.team_id == team.id,
                DutyEscalation.duty_user_id == duty_user.id,
            )
        )
    ).scalar_one_or_none()

    if not escalation:
        session.add(DutyEscalation(team_id=team.id, duty_user_id=duty_user.id, level=0))

    await session.commit()
    await session.refresh(duty_user)
    return duty_user


# === Смены ===
async def get_shift_by_date(
    session: AsyncSession, duty_user_id: int, date_: date
) -> Optional[DutyShift]:
    """Смена пользователя на конкретную дату."""
    stmt = (
        select(DutyShift)
        .options(
            selectinload(DutyShift.duty_user).selectinload(DutyUser.user),
            selectinload(DutyShift.team),
        )
        .where(
            DutyShift.duty_user_id == duty_user_id,
            DutyShift.starts_at >= datetime.combine(date_, datetime.min.time()),
            DutyShift.starts_at <= datetime.combine(date_, datetime.max.time()),
        )
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_user_shifts(
    session: AsyncSession,
    duty_user_id: int,
    period: str = PERIOD_WEEK,
    base_date: date | None = None,
) -> List[DutyShift]:
    """Смены конкретного дежурного (по периоду, можно указать базовую дату)."""
    stmt = (
        select(DutyShift)
        .options(
            selectinload(DutyShift.duty_user).selectinload(DutyUser.user),
            selectinload(DutyShift.team),
        )
        .where(DutyShift.duty_user_id == duty_user_id)
        .order_by(DutyShift.starts_at)
    )

    filt = _period_filter(period, base_date)
    if filt is not None:
        stmt = stmt.where(filt)

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_user_shifts_by_date(
    session: AsyncSession,
    duty_user_id: int,
    date_: date | None = None,
    period: str | None = None,
) -> List[DutyShift]:
    """Смены пользователя за день/неделю/месяц относительно date_ (по умолчанию — сегодня)."""
    now = date_ or date.today()
    start, end = _get_period_range(now, period or PERIOD_DAY)

    stmt = (
        select(DutyShift)
        .options(
            selectinload(DutyShift.duty_user).selectinload(DutyUser.user),
            selectinload(DutyShift.team),
        )
        .where(
            DutyShift.duty_user_id == duty_user_id,
            DutyShift.starts_at >= start,
            DutyShift.starts_at < end,
        )
        .order_by(DutyShift.starts_at)
    )
    return (await session.execute(stmt)).scalars().all()


async def get_team_shifts(
    session: AsyncSession,
    team_id: Optional[int] = None,
    period: str = PERIOD_MONTH,
    base: Optional[date] = None,
) -> List[DutyShift]:
    """Смены команды (по team_id и периоду относительно base)."""
    stmt = (
        select(DutyShift)
        .options(
            selectinload(DutyShift.duty_user).selectinload(DutyUser.user),
            selectinload(DutyShift.team),
        )
        .order_by(DutyShift.starts_at)
    )

    if team_id:
        stmt = stmt.where(DutyShift.team_id == team_id)

    filt = _period_filter(period, base)
    if filt is not None:
        stmt = stmt.where(filt)

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_team_shifts_by_date(
    session: AsyncSession, team_id: int, date_: date
) -> List[DutyShift]:
    """Все смены команды на дату."""
    stmt = (
        select(DutyShift)
        .options(
            selectinload(DutyShift.duty_user).selectinload(DutyUser.user),
            selectinload(DutyShift.team),
        )
        .where(
            DutyShift.team_id == team_id,
            DutyShift.starts_at >= datetime.combine(date_, datetime.min.time()),
            DutyShift.starts_at <= datetime.combine(date_, datetime.max.time()),
        )
        .order_by(DutyShift.starts_at)
    )
    return (await session.execute(stmt)).scalars().all()


async def assign_shift(
    session: AsyncSession,
    duty_user_id: int,
    team_id: int,
    starts_at: datetime,
    ends_at: datetime,
    role: str = "primary",
) -> DutyShift:
    """Назначить смену пользователю (проверка пересечений)."""
    overlap = (
        await session.execute(
            select(DutyShift).where(
                DutyShift.duty_user_id == duty_user_id,
                DutyShift.starts_at < ends_at,
                DutyShift.ends_at > starts_at,
            )
        )
    ).scalar_one_or_none()

    if overlap:
        raise ValueError("⚠ У пользователя уже есть смена в этот интервал.")

    shift = DutyShift(
        duty_user_id=duty_user_id,
        team_id=team_id,
        starts_at=starts_at,
        ends_at=ends_at,
        role=role,
    )
    session.add(shift)
    await session.commit()
    await session.refresh(shift)
    return shift


async def remove_shift(session: AsyncSession, shift_id: int) -> bool:
    """Удалить смену по id."""
    shift = (
        await session.execute(select(DutyShift).where(DutyShift.id == shift_id))
    ).scalar_one_or_none()
    if not shift:
        return False

    await session.delete(shift)
    await session.commit()
    return True


# === Обмен сменами ===
async def request_swap(session: AsyncSession, duty_user_id: int, shift_id: int) -> DutySwapRequest:
    """Создать запрос на обмен смены."""
    swap = DutySwapRequest(from_user_id=duty_user_id, shift_id=shift_id)
    session.add(swap)
    await session.commit()
    await session.refresh(swap)
    return swap


async def confirm_swap(session: AsyncSession, swap_id: int, to_user_id: int) -> bool:
    """Подтвердить обмен смены (смена закрепляется за новым пользователем)."""
    swap = (
        await session.execute(select(DutySwapRequest).where(DutySwapRequest.id == swap_id))
    ).scalar_one_or_none()

    if not swap or swap.status != "pending":
        return False

    swap.shift.duty_user_id = to_user_id
    swap.status = "confirmed"

    await session.commit()
    return True
