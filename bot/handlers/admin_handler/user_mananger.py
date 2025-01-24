from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from api.services import UserService
from bot.constants import MenuLabels
from bot.constants.states import UserCommands
from bot.keyboards import in_back_keyboard
from bot.utils import HelperFunctions, StateManager
from bot.utils.logger_instance import app_logger

router = Router()
# Максимальное количество строк на одной странице
ROWS_PER_PAGE = 20

async def generate_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для пагинации с выделением текущей страницы."""
    keyboard = InlineKeyboardMarkup(row_width=5, inline_keyboard=[])

    # Диапазон страниц для отображения в навигации
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    # Кнопки навигации
    navigation_buttons = [
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page - 1}") if page > 1 else None,
        *[
            InlineKeyboardButton(text=str(i), callback_data=f"page_{i}") if i != page
            else InlineKeyboardButton(text=f"⟨ {i} ⟩", callback_data="current_page")
            for i in range(start_page, end_page + 1)
        ],
        InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"page_{page + 1}") if page < total_pages else None
    ]

    # Фильтрация None и добавление кнопок
    keyboard.inline_keyboard.append([button for button in navigation_buttons if button])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text=MenuLabels.BACK.value, callback_data="back")])
    return keyboard

@router.message(F.text == MenuLabels.VIEW_USERS.value)
async def view_users(message: Message, state: FSMContext):
    """Отображает список пользователей."""
    action = f"{__name__}.view_users"
    current_date = HelperFunctions.get_current_date()
    try:
        # Получаем всех пользователей
        users_data = await UserService.get_all_users()

        # Если данные пустые, информируем пользователя
        if not users_data:
            await message.reply(
                "В базе нет пользователей.",
                reply_markup=in_back_keyboard,
                parse_mode="HTML",
            )
            return

        # Фильтруем только нужные поля для каждого пользователя
        filtered_users_data = [
            {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company_post': user.company_post,
                'phone_number': user.phone_number,
                'email': user.email
            }
            for user in users_data
        ]

        # Логируем отфильтрованные данные
        app_logger.info("Filtered Users %s", filtered_users_data)

        # Формируем таблицу с отфильтрованными данными
        table_output = HelperFunctions.table_formatted_output(filtered_users_data, [])

        # Разбиваем таблицу на строки
        table_lines = table_output.splitlines()

        # Рассчитываем количество страниц
        total_pages = (len(table_lines) - 1) // ROWS_PER_PAGE + 1
        app_logger.info(table_output)
        app_logger.info(table_lines)

        # Устанавливаем текущую страницу и сохраняем данные в состоянии
        page = 1
        await state.update_data(table_lines=table_lines, total_pages=total_pages, page=page)

        # Отправляем пользователю данные текущей страницы
        await send_page(message, state, page, total_pages, current_date)

    except Exception as e:
        HelperFunctions.log_error(action=action, error=e)
        await message.reply(
            "Ошибка при загрузке пользователей.",
            reply_markup=in_back_keyboard,
            parse_mode="HTML",
        )

async def send_page(message: Message, state: FSMContext, page: int, total_pages: int, current_date: str):
    """Отправляет одну страницу с состоянием портов."""
    data = await state.get_data()
    table_lines = data.get('table_lines', [])
    start = (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE
    page_content = "\n".join(table_lines[start:end])

    # Сообщение с текущей страницей
    full_message = (
        f"Пользователи системы:\n"
        f"<pre>{page_content}\n</pre>\n\n"
        f"<i>Страница {page} из {total_pages}</i>\n"
        f"<i>Выполнено: <code>{current_date}</code></i>"
    )

    # Клавиатура для пагинации
    pagination_keyboard = await generate_pagination_keyboard(page, total_pages)
    display_data = {"text": full_message, "reply_markup": pagination_keyboard}
    await StateManager.set_state_with_previous(state, UserCommands.USER_MENU, display_data)

    await message.reply(text=full_message, reply_markup=pagination_keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("page_"))
async def pagination_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик для пагинации с использованием callback."""
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    total_pages = data.get('total_pages', 1)
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Обновляем текущую страницу и отправляем новую страницу
    await state.update_data(page=page)
    await send_page(callback.message, state, page, total_pages, current_date)
    await callback.answer()
