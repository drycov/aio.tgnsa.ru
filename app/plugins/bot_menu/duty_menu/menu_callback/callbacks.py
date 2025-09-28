from __future__ import annotations

from datetime import date, datetime
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select

from app.core.db import get_sessionmaker
from app.core.utils.calendar import build_calendar
from app.models.duty import DutyUser
from app.models.user import User
from ..services.duty_service import (
    get_team_shifts_by_date,
    get_user_shifts_by_date,
    get_team_shifts,
)
logger = logging.getLogger(__name__)

router = Router()
session_maker = get_sessionmaker()


# 📅 Навигация по календарю (⬅ / ➡)
async def calendar_navigation_handler(callback: CallbackQuery, state: FSMContext):
    try:
        # e.g. "team_next:2025-10" | "view_prev:2025-04"
        action, payload = callback.data.split(":")
        context, _ = action.split("_")  # team | view | swap | confirm
        year, month = map(int, payload.split("-"))
        base = date(year, month, 1)

        async with session_maker() as session:
            if context == "team":
                # team_id лучше держать в state; пока берём из профиля
                stmt = select(DutyUser).join(User).where(User.tg_id == callback.from_user.id)
                duty_user = (await session.execute(stmt)).unique().scalar_one_or_none()
                if not duty_user or not duty_user.team_members:
                    await callback.answer("❌ Нет команды", show_alert=True)
                    return
                team_id = duty_user.team_members[0].team_id
                shifts = await get_team_shifts(session, team_id=team_id, period="month", base=base)
            else:
                # view/swap/confirm — считаем как личный календарь
                stmt = select(DutyUser).join(User).where(User.tg_id == callback.from_user.id)
                duty_user = (await session.execute(stmt)).unique().scalar_one_or_none()
                if not duty_user:
                    await callback.answer("❌ Нет профиля дежурного", show_alert=True)
                    return
                shifts = await get_user_shifts_by_date(session, duty_user.id, date_=base, period="month")

        kb = build_calendar(year, month, context, shifts)
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except TelegramBadRequest as e:
            # Ничего менять — значит уже тот же месяц и сетка идентична
            if "message is not modified" not in str(e).lower():
                raise
        await callback.answer()

    except Exception as e:
        logger.exception(f"[calendar_navigation_handler] Ошибка: {e}")
        await callback.answer("⚠ Ошибка при обновлении календаря", show_alert=True)


# 📅 Выбор даты
# 📅 Выбор даты
async def calendar_date_selected(callback: CallbackQuery, state: FSMContext):
    try:
        action, date_str = callback.data.split(":")
        context = action.split("_")[0]  # view | team | swap | confirm
        date_obj = date.fromisoformat(date_str)

        async with session_maker() as session:
            stmt = select(DutyUser).join(User).where(User.tg_id == callback.from_user.id)
            duty_user = (await session.execute(stmt)).unique().scalar_one_or_none()
            if not duty_user:
                await callback.answer("❌ Нет профиля дежурного", show_alert=True)
                return

            if context == "view":
                shifts = await get_user_shifts_by_date(
                    session, duty_user.id, date_=date_obj, period="day"
                )
                if shifts:
                    text = f"📅 Ваши смены {date_str}:\n" + "\n".join(
                        f"🕘 {s.starts_at:%H:%M}-{s.ends_at:%H:%M} "
                        f"({getattr(s, 'role', 'primary')}) | {s.team.name}"
                        for s in shifts
                    )
                    await callback.answer(text, show_alert=True)
                else:
                    await callback.answer(f"❌ У вас нет смен на {date_str}", show_alert=True)

            elif context == "team":
                if not duty_user.team_members:
                    await callback.answer("❌ Нет команды", show_alert=True)
                    return

                team_id = duty_user.team_members[0].team_id
                shifts = await get_team_shifts_by_date(session, team_id=team_id, date_=date_obj)

                if shifts:
                    text = f"👥 Смены команды {date_str}:\n" + "\n".join(
                        f"👤 {s.duty_user.full_name} | "
                        f"🕘 {s.starts_at:%H:%M}-{s.ends_at:%H:%M} "
                        f"({getattr(s, 'role', 'primary')})"
                        for s in shifts
                    )
                    await callback.answer(text, show_alert=True)
                else:
                    await callback.answer("❌ Нет смен у команды", show_alert=True)

    except Exception as e:
        logger.exception(f"[calendar_date_selected] Ошибка: {e}")
        await callback.answer("⚠ Ошибка выбора даты", show_alert=True)


def register_callbacks(dp_or_router) -> None:
    dp_or_router.callback_query.register(
        calendar_navigation_handler,
        F.data.startswith((
            "view_prev", "view_next",
            "swap_prev", "swap_next",
            "confirm_prev", "confirm_next",
            "team_prev", "team_next",
        )),
    )
    dp_or_router.callback_query.register(
        calendar_date_selected,
        F.data.startswith((
            "view_calendar", "swap_calendar",
            "confirm_calendar", "team_calendar",
        )),
    )
