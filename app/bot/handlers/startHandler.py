from typing import Dict, Any, Union

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from app.bot.constants.labels import MenuLabels
from app.bot.fsm.state_manager import StateManager
from app.bot.constants.messages import ContextHelp, Messages
from app.bot.handlers.register_handlers.registration_handler import start_registration
from app.bot.keyboards.main import generate_main_keyboard
from app.bot.keyboards.base import build_auth_keyboard, on_enter_keyboard
from app.core.config import logger
from app.exceptions.exceptions import UserNotFoundError
from app.services.user import UserSearchField, UserService
from app.core.utils.decorators import safe_delete_message
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.message(CommandStart())
@safe_delete_message
async def handle_start(message: Message, state: FSMContext, db: AsyncSession) -> None:
    """
    Обработчик команды /start с поддержкой восстановления предыдущего состояния.

    Args:
        message: Входящее сообщение
        state: Контекст FSM
    """
    user_id = message.from_user.id
    data = await state.get_data()
    service = UserService(db)
    try:
        user = await service.get_user(user_id, UserSearchField.TG_ID)
        if not user.is_authorized:
            await service.set_authorized(user_id, False)
    except UserNotFoundError:
        logger.warning(
            f"[main_menu] 🚫 User not authorized or not found: tg_id={user_id}"
        )
        await message.answer(
            Messages.PLEASE_ENTER.value, reply_markup=on_enter_keyboard
        )
        await start_registration(message, state)
        return

    except Exception as e:
        logger.exception(f"[main_menu] ❌ Unexpected error while loading user: {e}")
        await message.answer(Messages.INTERNAL_ERROR.value)
        return

    # Логирование начала обработки
    logger.debug(f"[START] Handling start command for user {user_id}")

    try:
        if await _try_restore_previous_state(state, message):
            logger.info(f"[START] Restored previous state for user {user_id}")
        else:
            await _show_main_menu(data, state, message)
            logger.info(f"[START] Showed main menu for user {user_id}")
    except Exception as e:
        logger.error(f"[START] Error for user {user_id}: {e}")
        await _handle_start_error(message)


async def _try_restore_previous_state(state: FSMContext, message: Message) -> bool:
    """
    Пытается восстановить предыдущее состояние с использованием StateManager.

    Args:
        state: Контекст FSM
        message: Сообщение от пользователя

    Returns:
        bool: True — если предыдущий переход выполнен, иначе False.
    """
    data = await state.get_data()
    if data.get("previous_state"):
        await StateManager.handle_back_action(state, message)
        return True
    return False


async def _show_main_menu(
    data: Dict[str, Any], state: FSMContext, message: Message
) -> None:
    """Показывает главное меню пользователю."""
    await state.set_state(None)  # Сброс состояния
    keyboard = build_auth_keyboard(is_authenticated=data.get("is_admin", False))
    await message.answer(text=Messages.WELCOME.value, reply_markup=keyboard)


async def _handle_start_error(message: Message) -> None:
    """Обрабатывает ошибки при старте."""
    await message.answer(
        text="⚠️ Произошла ошибка. Попробуйте еще раз.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("cancel"))
@safe_delete_message
async def cancel_registration(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /cancel для отмены текущего действия.

    Args:
        message: Входящее сообщение
        state: Контекст FSM
    """
    user_id = message.from_user.id
    logger.info(f"[CANCEL] Cancelling action for user {user_id}")

    await state.clear()
    await message.answer(
        text=f"{Messages.CANCELLED.value}\nЧтобы продолжить, нажмите кнопку ниже.",
        reply_markup=on_enter_keyboard,
    )


@router.message(F.text == MenuLabels.BACK.value)
@router.callback_query(F.data == "back")
@safe_delete_message
async def handle_back_command(
    event: Union[Message, CallbackQuery], state: FSMContext, db: AsyncSession
) -> None:
    """
    Обработчик команды "Назад" с:
    - Отправкой только новых сообщений (без редактирования)
    - Поддержкой как сообщений, так и callback
    - Полной обработкой ошибок
    """
    user_id = event.from_user.id
    is_callback = isinstance(event, CallbackQuery)

    logger.info(
        f"[BACK] {'Callback' if is_callback else 'Message'} from user {user_id}"
    )

    try:
        # Получаем объект сообщения для работы
        message = event.message if is_callback else event
        service = UserService(db)

        # Обрабатываем действие "Назад"
        result = await StateManager.handle_back_action(state, message)

        if isinstance(result, dict) and "text" in result:
            # Всегда отправляем новое сообщение
            await message.answer(**result)
        else:
            # Возврат в главное меню
            # logger.info(f"[BACK] Showing main menu for user {user_id}")
            is_admin = await service.is_admin(user_id)
            logger.debug(f"[BACK] User {user_id} is_admin: {is_admin}")

            keyboard = generate_main_keyboard(is_admin=is_admin)
            await state.clear()
            await message.answer(text=Messages.WELCOME.value, reply_markup=keyboard)

        # Для callback всегда отвечаем, чтобы убрать часики
        if is_callback:
            await event.answer()

    except Exception as e:
        logger.exception(f"[BACK] Error for user {user_id}: {e}")
        error_msg = "⚠️ Ошибка при возврате. Попробуйте ещё раз."

        try:
            target = event.message if is_callback else event
            await target.answer(error_msg)
        except Exception as answer_error:
            logger.error(f"[BACK] Failed to send error message: {answer_error}")

        if is_callback:
            await event.answer()


@router.message(Command("help"))
@safe_delete_message
async def handle_help(message: Message, state: FSMContext) -> None:
    """
    Улучшенный обработчик команды /help с:
    - Контекстно-зависимой помощью
    - Поддержкой полной справки
    - Обработкой ошибок
    """
    try:
        current_state = await state.get_state()
        help_text = ContextHelp.get_help_for_state(current_state)

        # Добавляем кнопку для полной справки
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📚 Полная справка", callback_data="full_help"
                    )
                ]
            ]
        )

        await message.answer(text=help_text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Help command error for user {message.from_user.id}: {e}")
        await message.answer("⚠️ Не удалось загрузить справку. Попробуйте позже.")


@router.callback_query(F.data == "full_help")
async def send_full_help(callback: CallbackQuery) -> None:
    """Обработчик полной справки"""
    try:
        await callback.message.edit_text(
            text=ContextHelp.get_full_help(), parse_mode="Markdown", reply_markup=None
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Full help error for user {callback.from_user.id}: {e}")
        await callback.answer("⚠️ Ошибка загрузки полной справки", show_alert=True)
