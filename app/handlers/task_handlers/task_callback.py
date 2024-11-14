from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.constants.states import TaskPaginationState
from app.handlers.task_handlers.task_manager import view_tasks
from app.models import Task

router = Router()


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
        await view_tasks(callback_query.message, created_by=user_id, page=page, edit=True, action='view')
    elif user_role.get("role") == "all":
        await view_tasks(callback_query.message, page=page, edit=True, action='view')
    else:
        await view_tasks(callback_query.message, assigned_to=user_id, page=page, edit=True, action='view')

    # Подтверждаем обработку колбэка
    await callback_query.answer()


# Обработчик для принятия задачи
@router.callback_query(lambda call: call.data.startswith("accept_task_"))
async def accept_task(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    task = Task.update_task_status(task_id, "accepted")
    if task:
        await callback_query.answer("Задача принята.")
        await view_tasks(callback_query.message, task_id=task_id, edit=True)

    else:
        await callback_query.answer("Ошибка при принятии задачи.", show_alert=True)
        await view_tasks(callback_query.message, task_id=task_id, edit=True)


# Обработчик для завершения задачи
@router.callback_query(lambda call: call.data.startswith("complete_task_"))
async def complete_task(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    task = Task.update_task_status(task_id, "completed")
    if task:
        await callback_query.answer("Задача завершена.")
        await callback_query.message.edit_reply_markup()
        await view_tasks(callback_query.message, task_id=task_id, edit=True)

    else:
        await callback_query.answer("Ошибка при завершении задачи.", show_alert=True)
        await view_tasks(callback_query.message, task_id=task_id, edit=True)


# Обработчик для отзыва задачи
@router.callback_query(lambda call: call.data.startswith("revoke_task_"))
async def revoke_task(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    task = Task.update_task_status(task_id, "revoked")
    if task:
        await callback_query.answer("Задача отозвана.")
        await callback_query.message.edit_reply_markup()

        await view_tasks(callback_query.message, task_id=task_id, edit=True)

    else:
        await callback_query.answer("Ошибка при отзыве задачи.", show_alert=True)
        await view_tasks(callback_query.message, task_id=task_id, edit=True)


# Обработчик для редактирования задачи
@router.callback_query(lambda call: call.data.startswith("edit_task_"))
async def edit_task(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    # Здесь можно перейти в режим редактирования задачи, например, запрашивать новые данные
    await callback_query.answer("Переход к редактированию задачи.")
    await callback_query.message.edit_reply_markup()  # Убираем клавиатуру после действия
