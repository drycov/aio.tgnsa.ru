from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.bot.constants.labels import MenuLabels
from app.core.utils.decorators import safe_delete_message
from app.services.user import UserSearchField, UserService
from sqlalchemy.ext.asyncio import AsyncSession
from app.exceptions.exceptions import UserNotFoundError, UserBannedError
from app.core.config import settings
router = Router()


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
        is_owner = tg_id == settings.bot.owner_id
        is_superuser = tg_id in settings.bot.superusers
        is_admin = tg_id in settings.bot.ADMINS

        # Блок привилегий — показывается только владельцу, суперу или админу
        privileges = []
        if is_owner:
            privileges.append("🛡️ <b>Владелец</b>")
        if is_superuser:
            privileges.append("👑 Суперпользователь")
        if is_admin:
            privileges.append("🧑‍💼 Администратор")

        privilege_text = ""
        if any([is_owner, is_superuser, is_admin]):
            privilege_text = "\n\n<b>Привилегии:</b>\n" + "\n".join(privileges)

        # Доп. информация — только для тех же групп
        debug_info = ""
        if any([is_owner, is_superuser, is_admin]):
            debug_info = (
                f"\n\n<b>Служебная информация:</b>\n"
                f"🆔 TG ID: <code>{user.tg_id}</code>\n"
                f"🗂️ ID пользователя: <code>{user.id}</code>\n"
                f"📅 Зарегистрирован: {user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else '—'}\n"
            )

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
        await message.answer("⚠️ Ошибка при получении профиля.")
        raise
