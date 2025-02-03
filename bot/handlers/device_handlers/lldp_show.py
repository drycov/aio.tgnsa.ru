from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardRemove, CallbackQuery

from bot.constants import MenuLabels, ErrorMessages
from bot.constants.states import DeviceCommands
from bot.keyboards import in_back_keyboard
from bot.utils import HelperFunctions, DeviceUtils, StateManager
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


@router.message(F.text == MenuLabels.DEVICE_LLDP.value)
async def lldp_info(message: Message, state: FSMContext):
    """
        Вывод уровня оптического сигнала/ADSL на устройстве через Telegram-бота.
    """
    action = f"{__name__}.lldp_info"
    current_date = HelperFunctions.get_current_date()
    data = await state.get_data()
    host = data.get('host')
    community = data.get('community')
    try:
        #             ], dtype=[('local_if_name', 'U50'), ('if_name', 'U50'), ('sys_name', 'U50'), ('sys_model', 'U50')])

        lldp_info = await DeviceUtils.get_lldp_data(host, community)
        table_output = HelperFunctions.table_formatted_output(lldp_info, ["LocalPort", "RemotePort", "RemoteSysName", "RemoteSysModel"])
        table_lines = table_output.splitlines()
        total_pages = (len(table_lines) - 1) // ROWS_PER_PAGE + 1  # Рассчитываем количество страниц
        page = 1
        app_logger.info(lldp_info)
        await state.update_data(table_lines=table_lines, total_pages=total_pages, page=page)
        await send_page(message, state, page, total_pages, host, current_date)

    except Exception as e:
                    HelperFunctions.log_error(action=action, error=e, host=host)
                    await message.reply(
                        "Ошибка",
                        reply_markup=in_back_keyboard,
                        parse_mode="HTML",
                    )


async def send_page(message: Message, state: FSMContext, page: int, total_pages: int, host: str, current_date: str,
                    ):
    """Отправляет одну страницу с состоянием портов."""
    data = await state.get_data()
    table_lines = data.get('table_lines', [])
    start = (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE
    page_content = "\n".join(table_lines[start:end])

    # Сообщение с текущей страницей
    full_message = (
        f"Соседнее оборудование по LLDP для устройства: <code>{host}</code>\n"
        f"<pre>{page_content}\n</pre>\n\n"
        f"<i>Страница {page} из {total_pages}</i>\n"
        f"<i>Выполнено: <code>{current_date}</code></i>"
    )

    # Клавиатура для пагинации
    pagination_keyboard = await generate_pagination_keyboard(page, total_pages)
    display_data = {"text": full_message, "reply_markup": pagination_keyboard}
    await StateManager.set_state_with_previous(state, DeviceCommands.PORT_INFORMATION, display_data)

    await message.reply(text=full_message, reply_markup=pagination_keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("page_"))
async def pagination_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик для пагинации с использованием callback."""
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    total_pages = data.get('total_pages', 1)
    host = data.get('host')
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Обновляем текущую страницу и отправляем новую страницу
    await state.update_data(page=page)
    await send_page(callback.message, state, page, total_pages, host, current_date)
    await callback.answer()
