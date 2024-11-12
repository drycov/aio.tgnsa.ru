from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, Message
from loguru import logger
from tabulate import tabulate

from app.bot_instance import bot
from app.constants import Messages, MenuLabels
from app.constants.states import MainCommands, RegistrationForm, TaskPaginationState
from app.handlers.shedule_handlers.task_manager import view_tasks
from app.keyboards import on_enter_keyboard
from app.models import User, Task
from app.utils import StateManager, CalendarMarkup
from config import Config

router = Router()


# @router.callback_query(lambda c: c.data == "back")
# async def back_callback(callback_query: CallbackQuery, state: FSMContext):
#     """
#     Обработчик для возврата на предыдущий шаг при нажатии кнопки с callback_data="back".
#     """
#     await StateManager.return_to_previous_state(state, callback_query=callback_query)

@router.message(F.text == MenuLabels.BACK.value)  # Обработчик для текстовой команды "Назад"
async def back_command_text(message: Message, state: FSMContext):
    await StateManager.handle_back_action(state, message)


@router.callback_query(F.data == "back")  # Обработчик для callback_query с данными "back"
async def back_command_callback(callback_query: CallbackQuery, state: FSMContext):
    await StateManager.handle_back_action(state, callback_query.message)
    await callback_query.answer()  # Закрывает окно callback


@router.callback_query(lambda c: c.data == "approve_user")
async def approve_user(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Ваши данные подтверждены!")
    logger.info(f"Пользователь {callback_query.from_user.id} подтвердил свои данные.")

    # Сбор данных пользователя из состояния
    user_data = await state.get_data()
    verification_code = User.generate_verification_code()
    user_hash = User.generate_hash(verification_code)
    logger.info(f"Код подтверждения: {verification_code}")

    try:
        # Создаем новый объект User
        new_user = User(
            is_bot=callback_query.from_user.is_bot,
            tg_id=callback_query.from_user.id,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            company_post=user_data['company_post'],
            phone_number=user_data['phone_number'],
            username=callback_query.from_user.username or f"u{callback_query.from_user.id}",
            is_admin=False,
            is_allowed=False,
            is_verified=False,
            verification_code=verification_code,
            email=user_data['email'],
            hash=user_hash
        )

        # Данные для таблицы
        table_data = [
            ["Telegram ID", new_user.tg_id],
            ["Username", new_user.username],
            ["Полное имя", f"{new_user.first_name} {new_user.last_name}"],
            ["Должность", new_user.company_post],
            ["Phone", new_user.phone_number],
            ["E-Mail", new_user.email],
            ["Подтвердить", f"/approve_{callback_query.from_user.id}"],
            ["Отклонить", f"/reject_{callback_query.from_user.id}"]
        ]

        # Создание таблицы из данных
        table_str = tabulate(table_data, tablefmt="plain")
        admin_message = f"Новый пользователь ожидает подтверждения:\n\n{table_str}"

        # Сохранение пользователя в базу данных
        User.create(new_user.model_dump())
        await callback_query.message.answer(Messages.USER_SAVED_IN_DB.value, reply_markup=on_enter_keyboard,
                                            parse_mode="HTML")

        # Проверка наличия admin ID
        admin_id = Config.DEFAULT_ADMIN_ID
        if admin_id is None:
            logger.error("DEFAULT_ADMIN_ID не задан в конфигурации.")
            await callback_query.answer(Messages.ERROR_GENERAL.value, parse_mode="HTML")
            return

        # Отправка таблицы с данными пользователя администратору
        try:
            await bot.send_message(admin_id, admin_message, parse_mode="HTML")
        except Exception as send_error:
            logger.error(f"Ошибка при отправке сообщения администратору (chat_id={admin_id}): {send_error}")

    except Exception as e:
        logger.error(f"Ошибка при создании пользователя с tg_id {callback_query.from_user.id}: {e}")
        await callback_query.answer(Messages.ERROR_GENERAL.value, parse_mode="HTML")

    # Очищаем состояние после завершения регистрации
    await state.clear()
    await state.set_state(MainCommands.START)


@router.callback_query(lambda c: c.data == "reject_user")
async def reject_user(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Пожалуйста, повторите ввод данных.")
    logger.info(f"Пользователь {callback_query.from_user.id} отклонил свои данные.")
    await callback_query.message.edit_text("Ваши данные отклонены. Пожалуйста, начните регистрацию заново.")

    await StateManager.set_state_with_previous(state, RegistrationForm.first_name)
    await bot.send_message(callback_query.from_user.id, Messages.REGISTER_FIRST_NAME.value,
                           reply_markup=ReplyKeyboardRemove())


# Обработчик для навигации по месяцам
@router.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
async def navigate_month(callback_query: CallbackQuery):
    _, year, month = callback_query.data.split("_")
    year, month = int(year), int(month)

    # Определяем направление навигации
    direction = "next" if "next_" in callback_query.data else "prev"

    # Создаем объект календаря и обновляем месяц
    calendar = CalendarMarkup(year, month)
    updated_calendar = calendar.update_calendar(direction)

    # Обновляем сообщение с новым календарем
    await callback_query.message.edit_reply_markup(reply_markup=updated_calendar)
    await callback_query.answer()  # Закрываем callback-запрос


# @router.callback_query(lambda call: call.data.startswith("view_tasks_"))
# async def handle_view_tasks_pagination(callback_query: CallbackQuery):
#     # Извлекаем номер страницы из callback_data
#     page = int(callback_query.data.split("_")[2])
#     await view_tasks(callback_query.message, page=page, edit=True)
#     await callback_query.answer()

# Callback для пагинации с учетом FSM
@router.callback_query(F.data.startswith("view_tasks_"), TaskPaginationState.viewing_tasks)
async def paginate_tasks(callback_query: CallbackQuery, state: FSMContext):
    # Извлекаем номер страницы из callback_data
    page = int(callback_query.data.split("_")[-1])
    user_id = int(callback_query.from_user.id)

    # Получаем текущую роль пользователя из состояния FSM
    user_role = await state.get_data()

    # В зависимости от роли пользователя фильтруем задачи
    if user_role.get("role") == "creator":
        await view_tasks(callback_query.message, created_by=user_id, page=page, edit=True)
    elif user_role.get("role") == "all":
        await view_tasks(callback_query.message, page=page, edit=True)
    else:
        await view_tasks(callback_query.message, assigned_to=user_id, page=page, edit=True)

    # Подтверждаем обработку колбэка
    await callback_query.answer()


# Обработчик для принятия задачи
@router.callback_query(lambda call: call.data.startswith("accept_task_"))
async def accept_task(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    task = Task.update_task_status(task_id, "accepted")
    if task:
        await callback_query.answer("Задача принята.")
        await view_tasks(callback_query.message,task_id=task_id, edit=True)

    else:
        await callback_query.answer("Ошибка при принятии задачи.", show_alert=True)
        await view_tasks(callback_query.message,task_id=task_id, edit=True)



# Обработчик для завершения задачи
@router.callback_query(lambda call: call.data.startswith("complete_task_"))
async def complete_task(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    task = Task.update_task_status(task_id, "completed")
    if task:
        await callback_query.answer("Задача завершена.")
        await callback_query.message.edit_reply_markup()
        await view_tasks(callback_query.message,task_id=task_id, edit=True)

    else:
        await callback_query.answer("Ошибка при завершении задачи.", show_alert=True)
        await view_tasks(callback_query.message,task_id=task_id, edit=True)



# Обработчик для отзыва задачи
@router.callback_query(lambda call: call.data.startswith("revoke_task_"))
async def revoke_task(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    task = Task.update_task_status(task_id, "revoked")
    if task:
        await callback_query.answer("Задача отозвана.")
        await callback_query.message.edit_reply_markup()

        await view_tasks(callback_query.message,task_id=task_id, edit=True)

    else:
        await callback_query.answer("Ошибка при отзыве задачи.", show_alert=True)
        await view_tasks(callback_query.message,task_id=task_id, edit=True)



# Обработчик для редактирования задачи
@router.callback_query(lambda call: call.data.startswith("edit_task_"))
async def edit_task(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    # Здесь можно перейти в режим редактирования задачи, например, запрашивать новые данные
    await callback_query.answer("Переход к редактированию задачи.")
    await callback_query.message.edit_reply_markup()  # Убираем клавиатуру после действия
