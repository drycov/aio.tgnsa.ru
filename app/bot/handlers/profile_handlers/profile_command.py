from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants.labels import MenuLabels
from app.core.utils.decorators import safe_delete_message
from app.services.user import UserSearchField, UserService
from app.exceptions.exceptions import UserNotFoundError, UserBannedError
from app.core.config import settings
from app.core.logging_setup import configure_logger


router = Router()
logger = configure_logger().bind(component="ProfileHandler")


@router.message(F.text == "/profile")
@router.message(F.text.casefold() == MenuLabels.USER_PROFILE.value.casefold())
@safe_delete_message
async def handle_profile(message: Message, state: FSMContext, db: AsyncSession):
    tg_id = message.from_user.id
    service = UserService(db)

    try:
        user = await service.get_user(tg_id, UserSearchField.TG_ID)
        role_names = [role.name for role in user.roles]

        # Проверка привилегий
        is_owner = tg_id == settings.bot.OWNER_ID
        is_superuser = tg_id in getattr(settings.bot, "SUPERUSERS", [])
        is_admin_cfg = tg_id in getattr(settings.bot, "ADMINS", [])
        is_admin_role = any(r == "admin" for r in role_names)

        # Блок привилегий
        privileges = []
        if is_owner:
            privileges.append("🛡️ <b>Владелец</b>")
        if is_superuser:
            privileges.append("👑 Суперпользователь")
        if is_admin_cfg or is_admin_role:
            privileges.append("🧑‍💼 Администратор")

        privilege_text = ""
        if privileges:
            privilege_text = "\n\n<b>Привилегии:</b>\n" + "\n".join(privileges)

        # Debug-блок (для админов/суперов/владельца)
        debug_info = ""
        if privileges:
            debug_info = (
                f"\n\n<b>Служебная информация:</b>\n"
                f"🆔 TG ID: <code>{user.tg_id}</code>\n"
                f"🗂️ ID пользователя: <code>{user.id}</code>\n"
                f"📅 Зарегистрирован: "
                f"{user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else '—'}\n"
            )

        # Формируем профиль
        profile_text = (
            f"👤 <b>Профиль пользователя</b>\n\n"
            f"🔗 Имя: {user.full_name}\n"
            f"✉️ Email: {user.email}\n"
            f"📞 Телефон: {user.phone or '—'}\n"
            f"🏢 Отдел: {user.department or '—'}\n"
            f"💼 Должность: {user.company_post or '—'}\n"
            f"🔐 Роли: {', '.join(role_names) or '—'}\n"
            f"✅ Авторизован: {'Да' if user.is_authorized else 'Нет'}\n"
            f"{'🚫 <b>Заблокирован</b>' if user.is_banned else ''}"
            f"{privilege_text}"
            f"{debug_info}"
        )

        await message.answer(profile_text, parse_mode="HTML")

    except UserNotFoundError:
        await message.answer("❌ Профиль не найден. Зарегистрируйтесь через /start.")
    except UserBannedError:
        await message.answer("🚫 Вы были заблокированы. Обратитесь к администратору.")
    except Exception as e:
        logger.exception(f"[handle_profile] Ошибка: {e}")
        await message.answer("⚠️ Произошла внутренняя ошибка при получении профиля.")
