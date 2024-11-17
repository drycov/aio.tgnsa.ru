from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.constants import MenuLabels, Symbols, ErrorMessages
from ...constants.states import DeviceCommands
from ...keyboards import in_back_keyboard
from ...utils import HelperFunctions, DeviceUtils, StateManager
from ...utils.logger_instance import app_logger

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


@router.message(F.text == MenuLabels.PORT_STATUS.value)
async def port_info(message: Message, state: FSMContext):
    # Устанавливаем текущие и предыдущие ID контекста
    data = await state.get_data()
    host = data.get('host')
    community = data.get('community')
    model = data.get('model')
    port_if_list = data.get('device_data', {}).get('interfaceList', [])
    port_if_range = data.get('device_data', {}).get('interfaceRange', [])
    action = f"{__name__}.port_info"
    current_date = HelperFunctions.get_current_date()

    # Получаем диапазоны интерфейсов
    if port_if_range == 'auto':
        port_if_range = await DeviceUtils.get_interface_range(host, community)
    if port_if_list == 'auto':
        port_if_list = await DeviceUtils.get_interface_list(host, community)

    await message.answer(
        f"Проверка портов на устройстве: <code>{host}</code>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

    try:
        # Получение состояния портов
        port_status = await DeviceUtils.get_port_status(host, port_if_list, port_if_range, community, model)
        state_info = (
            f"P.S. Состояния: {Symbols.OK.value} - Линк есть, {Symbols.CABLE_CHECKED.value} - Линка нет, "
            f"{Symbols.STATUS_ADMIN_DISABLED.value} - Порт выключен, {Symbols.CABLE_NOT_PRESENT.value} - Неизвестно"
        )

        # Логирование успешного выполнения
        message_log = {
            "date": current_date,
            "action": action,
            "userId": data.get('userId'),
            "status": "done"
        }
        app_logger.info(message_log)

        # Форматируем таблицу и разбиваем на страницы
        table_output = HelperFunctions.table_formatted_output(port_status, ["IF", "St.", "Errors", "Description"])
        table_lines = table_output.splitlines()
        total_pages = (len(table_lines) - 1) // ROWS_PER_PAGE + 1  # Рассчитываем количество страниц
        page = 1

        # Сохраняем данные о страницах в состоянии
        await state.update_data(table_lines=table_lines, total_pages=total_pages, page=page)

        # Отправляем первую страницу
        await send_page(message, state, page, total_pages, host, current_date, state_info)

    except Exception as e:
        # Логирование ошибки
        HelperFunctions.log_error(action=action, host=host, error=e)
        # Отправка сообщения об ошибке
        await message.answer(
            ErrorMessages.UNKNOWN_ERROR_USER.value,
            reply_markup=in_back_keyboard,
            parse_mode="HTML"
        )


async def send_page(message: Message, state: FSMContext, page: int, total_pages: int, host: str, current_date: str,
                    state_info: str):
    """Отправляет одну страницу с состоянием портов."""
    data = await state.get_data()
    table_lines = data.get('table_lines', [])
    start = (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE
    page_content = "\n".join(table_lines[start:end])

    # Сообщение с текущей страницей
    full_message = (
        f"Состояние портов на устройстве: <code>{host}</code>\n"
        f"<pre>{page_content}\n\n{state_info}</pre>\n\n"
        f"<i>Страница {page} из {total_pages}</i>\n"
        f"<i>Выполнено: <code>{current_date}</code></i>"
    )

    # Клавиатура для пагинации
    pagination_keyboard = await generate_pagination_keyboard(page, total_pages)
    print(pagination_keyboard)
    display_data = {"text": full_message, "reply_markup": pagination_keyboard}
    print(full_message)
    print(display_data)

    await StateManager.set_state_with_previous(state, DeviceCommands.PORT_INFORMATION, display_data)

    await message.answer(**display_data, parse_mode="HTML")


@router.callback_query(F.data.startswith("page_"))
async def pagination_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик для пагинации с использованием callback."""
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    total_pages = data.get('total_pages', 1)
    host = data.get('host')
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state_info = (
        f"P.S. Состояния: {Symbols.OK.value} - Линк есть, {Symbols.CABLE_CHECKED.value} - Линка нет, "
        f"{Symbols.STATUS_ADMIN_DISABLED.value} - Порт выключен, {Symbols.CABLE_NOT_PRESENT.value} - Неизвестно"
    )

    # Обновляем текущую страницу и отправляем новую страницу
    await state.update_data(page=page)
    await send_page(callback.message, state, page, total_pages, host, current_date, state_info)
    await callback.answer()
