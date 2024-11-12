from datetime import datetime
from typing import Optional

from aiogram import Router, types, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from firebase_admin import db

from app.constants import MenuLabels, Symbols
from app.constants.states import TaskCreationState, TaskPaginationState
from app.keyboards import priority_kb, in_back_keyboard, task_keyboard
from app.models import Task, PriorityLevel, User
from app.utils import CalendarMarkup, HelperFunctions, StateManager

router = Router()


# Команда для создания новой задачи
@router.message(F.text == MenuLabels.TASK_MANAGER.value)
async def new_task(message: Message, state: FSMContext):
    display_data = {"text": MenuLabels.TASK_MANAGER.value, "reply_markup": task_keyboard}
    await StateManager.set_state_with_previous(state, TaskCreationState.TASK_MENU, display_data)
    await message.answer(**display_data)


# Обработчики команд
@router.message(F.text.startswith("/task_"))
async def view_task(message: Message, state: FSMContext):
    task_id = message.text.split("_")[-1]
    await view_tasks(message, task_id=task_id)
    await state.set_state(TaskPaginationState.viewing_tasks)


@router.message(F.text == MenuLabels.VIEW_MY_TASKS.value)
async def view_created_tasks(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await view_tasks(message, created_by=user_id)
    await state.update_data(role="creator")  # Устанавливаем роль "создатель"
    await state.set_state(TaskPaginationState.viewing_tasks)


@router.message(F.text == MenuLabels.VIEW_ASSIGNED_TASKS.value)
async def view_assigned_tasks(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await view_tasks(message, assigned_to=user_id)
    await state.update_data(role="assignee")  # Устанавливаем роль "исполнитель"
    await state.set_state(TaskPaginationState.viewing_tasks)


@router.message(F.text == MenuLabels.VIEW_ALL_TASKS.value)
async def view_assigned_tasks(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await view_tasks(message, assigned_to=user_id, created_by=user_id)
    await state.update_data(role="all")  # Устанавливаем роль "исполнитель"
    await state.set_state(TaskPaginationState.viewing_tasks)


@router.message(F.text == "/at")
async def view_all_tasks(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await view_tasks(message, page=1)
    await state.update_data(role="all")  # Устанавливаем роль "все"
    await state.set_state(TaskPaginationState.viewing_tasks)


# Команда для создания новой задачи
@router.message(F.text == MenuLabels.CREATE_TASK.value)
async def new_task(message: Message, state: FSMContext):
    await state.set_state(TaskCreationState.DATE)
    now = datetime.now()
    calendar_markup = CalendarMarkup(now.year, now.month).create_calendar()
    await message.answer(
        "Выберите дату задачи:",
        reply_markup=calendar_markup
    )


# Обработчик выбора даты
@router.callback_query(F.data.startswith("day_"), StateFilter(TaskCreationState.DATE))
async def set_task_date(callback_query: types.CallbackQuery, state: FSMContext):
    _, day, month, year = callback_query.data.split("_")
    selected_date = f"{year}-{month}-{day.zfill(2)}"
    await state.update_data(task_start_date=selected_date)
    await state.set_state(TaskCreationState.END_DATE)
    now = datetime.now()
    calendar_markup = CalendarMarkup(now.year, now.month).create_calendar()
    await callback_query.message.edit_text("Укажите дату окончания задачи:",
                                           reply_markup=calendar_markup)
    await callback_query.answer()


@router.callback_query(F.data.startswith("day_"), StateFilter(TaskCreationState.END_DATE))
async def set_task_end_date(callback_query: types.CallbackQuery, state: FSMContext):
    _, day, month, year = callback_query.data.split("_")
    end_date = f"{year}-{month}-{day.zfill(2)}"
    await state.update_data(task_end_date=end_date)

    await state.set_state(TaskCreationState.TITLE)
    await callback_query.message.edit_text("Введите заголовок задачи:")
    await callback_query.answer()


@router.message(StateFilter(TaskCreationState.TITLE))
async def set_task_title(message: Message, state: FSMContext):
    await state.update_data(task_title=message.text)
    await state.set_state(TaskCreationState.DESCRIPTION)
    await message.answer("Введите описание задачи:")


@router.message(StateFilter(TaskCreationState.DESCRIPTION))
async def set_task_description(message: Message, state: FSMContext):
    await state.update_data(task_description=message.text)
    await state.set_state(TaskCreationState.PRIORITY)
    await message.answer("Укажите приоритет задачи:", reply_markup=priority_kb)


def generate_employee_keyboard() -> InlineKeyboardMarkup:
    # Создаем список списков с кнопками
    kb_buttons = [
        [InlineKeyboardButton(text=f"{user.first_name} {user.last_name}", callback_data=f"employee_{user.tg_id}")]
        for user in User.get_all()
    ]

    # Создаем объект InlineKeyboardMarkup с inline_keyboard
    return InlineKeyboardMarkup(inline_keyboard=kb_buttons)


# Обработчик выбора приоритета
@router.callback_query(F.data.startswith("priority_"), StateFilter(TaskCreationState.PRIORITY))
async def set_task_priority(callback_query: types.CallbackQuery, state: FSMContext):
    priority = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    await state.update_data(task_priority=priority)
    await state.update_data(user_id=user_id)

    await state.set_state(TaskCreationState.EMPLOYEE)
    employee_kb = generate_employee_keyboard()
    print(employee_kb)
    await callback_query.message.edit_text("Выберите сотрудника для выполнения задачи:",
                                           reply_markup=employee_kb)
    await callback_query.answer()


# Обработчик выбора сотрудника и создание задачи
# Пример обновленной функции assign_employee для создания задачи и уведомления
@router.callback_query(F.data.startswith("employee_"), StateFilter(TaskCreationState.EMPLOYEE))
async def assign_employee(callback_query: types.CallbackQuery, state: FSMContext):
    employee_id = callback_query.data.split("_")[1]
    data = await state.get_data()

    # Проверка наличия всех необходимых данных для задачи
    required_keys = ["task_start_date", "task_end_date", "task_title", "task_priority", "task_description", "user_id"]
    if not all(key in data for key in required_keys):
        await callback_query.message.answer("Ошибка: отсутствуют данные для создания задачи.")
        return

    # Конвертация дат в datetime
    task_start_date = datetime.fromisoformat(data["task_start_date"])
    task_end_date = datetime.fromisoformat(data["task_end_date"])

    # Создание экземпляра задачи
    task = Task(
        date=task_start_date,
        end_date=task_end_date,
        created_by=str(data["user_id"]),
        assigned_to=employee_id,
        title=data["task_title"],
        priority=PriorityLevel[data["task_priority"].upper()],
        status="planned",
        description=data["task_description"]
    )

    # Сохранение задачи в Firestore
    save_task_to_firestore(task)

    # Уведомление назначенного сотрудника о задаче
    await notify_assignee(task, callback_query.bot)

    # Ответ о создании задачи
    await callback_query.message.edit_text(
        f"<b>Задача успешно создана!</b>\n\n"
        f"<b>Дата начала:</b> {task.date}\n"
        f"<b>Дата окончания:</b> {task.end_date}\n"
        f"<b>Приоритет:</b> {task.priority}\n"
        f"<b>Сотрудник:</b> {employee_id}\n"
        f"<b>Описание:</b> {task.description}",
        reply_markup=in_back_keyboard,
        parse_mode="HTML"
    )
    await callback_query.answer()
    await state.clear()


# Функция сохранения задачи в Firestore

def save_task_to_firestore(task: Task):
    task_id = HelperFunctions.generate_task_id(task)  # Генерация уникального task_id

    task_ref = db.reference(f'tasks/{task_id}')
    task_data = task.model_dump()
    task_data['date'] = task.date.isoformat()
    task_data['end_date'] = task.end_date.isoformat()
    task_data['created_by'] = task.created_by

    task_ref.set(task_data)


async def notify_assignee(task: Task, bot):
    assignee = None  # Инициализация assignee для избежания ошибок использования неинициализированной переменной
    try:
        assignee_id = int(task.assigned_to)  # Преобразование в int
        assignee = User.get_by_tg_id(assignee_id)

        if assignee:  # Проверка, что assignee был найден
            await bot.send_message(
                assignee.tg_id,
                f"Вам назначена новая задача:\nДата: {task.date}\nОписание: {task.description}\nПриоритет: {task.priority}"
            )
        else:
            print(f"Сотрудник с ID {assignee_id} не найден.")

    except TelegramAPIError as e:
        if assignee and "bot was blocked by the user" in str(e):
            print(f"Не удалось уведомить сотрудника {assignee.tg_id}, бот заблокирован.")
        else:
            print(f"Ошибка при уведомлении: {e}")
    except ValueError:
        print("Ошибка преобразования assigned_to в int. Убедитесь, что assigned_to содержит корректный ID.")


async def notify_task_approach(task: Task, bot):
    # Уведомление за день до начала задачи
    current_date = datetime.now()
    if (task.date - current_date).days == 1:
        assignee = User.get_by_tg_id(task.assigned_to)
        await bot.send_message(
            assignee.tg_id,
            f"Напоминание: Завтра начинается задача '{task.description}'"
        )


# Функция для формирования клавиатуры с действиями

def get_navigation_and_action_keyboard(task_data: dict, user_id: int, page: int,
                                       total_pages: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2, inline_keyboard=[])
    task_id, task_properties = None, None

    # Извлекаем ID задачи и её данные, если task_data содержит только одну задачу
    if len(task_data) == 1:
        task_id, task_properties = next(iter(task_data.items()))

    # Кнопки навигации по страницам
    if len(task_data) != 1:
        start_page = max(1, page - 2)
        end_page = min(total_pages, page + 2)
        navigation_buttons = [
            InlineKeyboardButton(text="⬅️", callback_data=f"view_tasks_{page - 1}") if page > 1 else None,
            *[
                InlineKeyboardButton(text=str(i), callback_data=f"view_tasks_{i}") if i != page
                else InlineKeyboardButton(text=f"⟨ {i} ⟩ <", callback_data="current_page")
                for i in range(start_page, end_page + 1)
            ],
            InlineKeyboardButton(text="➡️", callback_data=f"view_tasks_{page + 1}") if page < total_pages else None
        ]
        # Фильтруем None-элементы и добавляем навигацию в клавиатуру
        keyboard.inline_keyboard.append([button for button in navigation_buttons if button])

    # Кнопки действий, если данные задачи и пользователя указаны
    if task_properties:
        if task_properties.get('assigned_to') == user_id:
            # Кнопки для исполнителя задачи
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"{Symbols.CABLE_CHECKED.value} Принять задачу",
                                     callback_data=f"accept_task_{task_id}") if task_properties.get(
                    'status') == 'planned' else None,
                InlineKeyboardButton(text=f"{Symbols.OK.value} Завершить задачу",
                                     callback_data=f"complete_task_{task_id}") if task_properties.get(
                    'status') == 'accepted' else None,
            ])
        elif task_properties.get('created_by') == user_id and task_properties.get('status') == 'revoked':
            # Кнопки для создателя задачи
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"{Symbols.ACTION_CANCEL.value} Отозвать задачу",
                                     callback_data=f"revoke_task_{task_id}") if task_properties.get(
                    'status') != 'revoked' else None,
                InlineKeyboardButton(text=f"{Symbols.EMOJI_EDIT.value} Редактировать задачу",
                                     callback_data=f"edit_task_{task_id}")
            ])

    return keyboard


async def view_tasks(message: types.Message, created_by: Optional[int] = None, assigned_to: Optional[int] = None,
                     task_id: Optional[str] = None, page: int = 1, edit: bool = False):
    tasks_ref = db.reference('tasks')
    tasks_per_page = 3  # Количество задач на одной странице
    user_id = message.from_user.id
    tasks = {}
    task_data = None  # Определяем переменную task_data заранее

    if task_id:
        task_data = tasks_ref.child(task_id).get()
        if not task_data:
            await message.answer("Задача не найдена.")
            return
        tasks = {task_id: task_data}

    else:
        if created_by:
            all_tasks = tasks_ref.order_by_child("created_by").equal_to(created_by).get()
        elif assigned_to:
            all_tasks = tasks_ref.order_by_child("assigned_to").equal_to(assigned_to).get()
        else:
            all_tasks = tasks_ref.get()

        if isinstance(all_tasks, dict):
            if assigned_to:
                # Фильтруем задачи, исключая те, что имеют статус "revoked"
                tasks = {key: task for key, task in all_tasks.items() if
                         isinstance(task, dict) and task.get("status") != "revoked"}
            else:
                tasks = {key: task for key, task in all_tasks.items()}
        else:
            # Если данные не являются словарем, устанавливаем пустой словарь
            tasks = {}

    if not tasks:
        await message.answer("Нет задач, соответствующих вашему запросу.")
        return

    total_tasks = len(tasks)
    total_pages = (total_tasks + tasks_per_page - 1) // tasks_per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * tasks_per_page
    end_idx = start_idx + tasks_per_page
    tasks_to_display = list(tasks.items())[start_idx:end_idx]

    # Функция для получения иконки статуса
    def get_status_icon(status):
        status_icons = {
            "accepted": "✅",
            "completed": "🏁",
            "revoked": "⛔",
            "planned": "📝",  # Иконка для статуса по умолчанию
            # Добавьте другие статусы и иконки при необходимости
        }
        return status_icons.get(status, "❔")  # Возвращает "❔", если статус неизвестен

    # Формируем информацию о задачах с учетом статуса и добавлением иконки
    tasks_info = "\n\n".join([
        f"{get_status_icon(task.get('status'))} Задача: /task_{key}\n"
        f"{'Дата начала: ' + task.get('date', 'не задано') + '\n' if task.get('status') != 'revoked' or task_id == key else ''}"
        f"{'Дата окончания: ' + task.get('end_date', 'не задано') + '\n' if task.get('status') != 'revoked' or task_id == key else ''}"
        f"{'Описание: ' + task.get('description', 'не указано') + '\n' if task.get('status') != 'revoked' or task_id == key else ''}"
        f"{'Приоритет: ' + task.get('priority', 'не задан') + '\n' if task.get('status') != 'revoked' or task_id == key else ''}"
        # Информация об исполнителе, если статус не "revoked"
        f"{'Исполнитель: <a href=\"tg://user?id=' + str(task.get('assigned_to', 0)) + '\">' + (User.get_by_tg_id(task.get('assigned_to', 0)).first_name if User.get_by_tg_id(task.get('assigned_to', 0)) else 'не назначен') + ' ' + (User.get_by_tg_id(task.get('assigned_to', 0)).last_name if User.get_by_tg_id(task.get('assigned_to', 0)) else '') + '</a>\n' if task.get('status') != 'revoked' else ''}"
        # Информация о создателе задачи
        f"Создатель: <a href='tg://user?id={task.get('created_by', 0)}'>" +
        (User.get_by_tg_id(task.get('created_by', 0)).first_name if User.get_by_tg_id(
            task.get('created_by', 0)) else 'не указан') + ' ' +
        (User.get_by_tg_id(task.get('created_by', 0)).last_name if User.get_by_tg_id(
            task.get('created_by', 0)) else '') + "</a>\n"
        for idx, (key, task) in enumerate(tasks_to_display)
        if isinstance(task, dict)
        and (task_id == key or task.get("status") != "revoked")
    ])

    # Создаем кнопки навигации
    action_navigation_keyboard = get_navigation_and_action_keyboard(tasks, user_id, page, total_pages)

    # Отправка или редактирование сообщения
    if edit:
        await message.edit_text(f"<b>Найденные задачи (Страница {page}/{total_pages}):</b>\n\n{tasks_info}",
                                parse_mode="HTML", reply_markup=action_navigation_keyboard)
    else:
        await message.answer(f"<b>Найденные задачи (Страница {page}/{total_pages}):</b>\n\n{tasks_info}",
                             parse_mode="HTML", reply_markup=action_navigation_keyboard)
