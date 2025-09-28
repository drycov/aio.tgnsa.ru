from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from app.bot.fsm.state_manager import StateManager
from app.core.logging_setup import configure_logger
from app.core.utils.calendar import build_calendar
from app.core.utils.decorators import safe_delete_message
from app.models.duty import DutyUser
from app.models.user import User
from ..services.duty_service import ensure_duty_profile, get_team_shifts, get_user_shifts
from ..constants.menu_label import DutyMenuLabels
from ..constants.messsages import DutyMessages
from ..constants.menu import build_duty_menu
from ..constants.states import DutyStates
from app.core.db import get_sessionmaker

logger = configure_logger().bind(component=__name__)
router = Router()
session_maker = get_sessionmaker()


async def _get_duty_user(session, tg_id: int) -> DutyUser | None:
    stmt = select(DutyUser).join(User).where(User.tg_id == tg_id)
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none()


async def _set_state_and_respond(
    state: FSMContext,
    new_state,
    message: Message,
    text: str,
    reply_markup=None,
    extra_data: dict | None = None,
):
    display_data = {"text": text}
    if reply_markup:
        display_data["reply_markup"] = reply_markup

    await StateManager.set_state_with_history(state, new_state, display_data)
    await message.answer(**display_data)
    if extra_data:
        await state.update_data(**extra_data)


def register_handlers(router: Router):
    # 📅 Главное меню дежурств
    @router.message(F.text == DutyMenuLabels.MAIN.value)
    @safe_delete_message
    async def duty_menu_handler(message: Message, state: FSMContext):
        try:
            logger.info(f"[duty_menu] Пользователь {message.from_user.id} открыл главное меню")
            async with session_maker() as session:
                user = (
                    await session.execute(
                        select(User).where(User.tg_id == message.from_user.id)
                    )
                ).unique().scalar_one_or_none()

                if not user:
                    await message.answer("❌ Пользователь не найден в системе.")
                    return

                duty_user = await ensure_duty_profile(session, user)

            buttons = build_duty_menu("main")
            await _set_state_and_respond(
                state=state,
                new_state=DutyStates.MENU,
                message=message,
                text="📅 <b>Меню дежурств</b>\nВыберите действие:",
                reply_markup=buttons,
                extra_data={"section": "main", "duty_user_id": duty_user.id},
            )
        except Exception as e:
            logger.exception(f"[duty_menu_handler] Ошибка: {e}")
            await message.answer(DutyMessages.ERROR_UNKNOWN.value)

    # 👨‍💻 Мои смены (календарь месяца)
    @router.message(F.text == DutyMenuLabels.MY_SHIFTS.value)
    async def my_shifts_handler(message: Message, state: FSMContext):
        logger.info(f"[my_shifts] Пользователь {message.from_user.id} открыл 'Мои смены'")
        async with session_maker() as session:
            duty_user = await _get_duty_user(session, message.from_user.id)
            if not duty_user:
                await message.answer("❌ У вас нет профиля дежурного.")
                return

            # базовая дата = текущий месяц (или позже — хранить выбранный в state)
            base = datetime.now().date()
            shifts = await get_user_shifts(session, duty_user.id, period="month", base_date=base)

            now = datetime.now()
            kb = build_calendar(
                year=now.year,
                month=now.month,
                action="view",   # view_calendar:YYYY-MM-DD
                shifts=shifts,
            )

            await _set_state_and_respond(
                state=state,
                new_state=DutyStates.VIEW_SCHEDULE_MONTH,
                message=message,
                text="📅 <b>Ваши смены на месяц</b>\n🟢 — день, когда у вас назначена смена.",
                reply_markup=kb,
                extra_data={"section": "my_shifts", "duty_user_id": duty_user.id},
            )

    # 👥 Смены команды
    @router.message(F.text == DutyMenuLabels.TEAM_SCHEDULE.value)
    async def team_schedule_handler(message: Message, state: FSMContext):
        logger.info(f"[team_schedule] Пользователь {message.from_user.id} открыл 'Расписание команды'")
        async with session_maker() as session:
            duty_user = await _get_duty_user(session, message.from_user.id)
            if not duty_user or not duty_user.team_members:
                await message.answer("❌ У вас нет привязки к команде.")
                return

            team_id = duty_user.team_members[0].team_id
            base = datetime.now().date()
            team_shifts = await get_team_shifts(session, team_id=team_id, period="month", base=base)

            now = datetime.now()
            kb = build_calendar(
                year=now.year,
                month=now.month,
                action="team",   # team_calendar:YYYY-MM-DD
                shifts=team_shifts,
            )

            await _set_state_and_respond(
                state=state,
                new_state=DutyStates.VIEW_TEAM,
                message=message,
                text="👥 <b>Календарь смен команды</b>\n🟢 — у кого-то из команды есть смена.",
                reply_markup=kb,
                extra_data={"section": "team_schedule", "team_id": team_id},
            )
