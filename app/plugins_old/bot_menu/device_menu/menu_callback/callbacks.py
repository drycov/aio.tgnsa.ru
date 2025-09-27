import datetime
import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message,  CallbackQuery

from app.bot.fsm.state_manager import StateManager
from app.bot.keyboards.base import in_back_keyboard
from app.core.logging_setup import logger
from app.core.utils.decorators import safe_delete_message
from ..constants.menu import generate_pagination_keyboard

from ..constants.menu_label import MenuLabels, Symbols
from ..constants.messages import Messages
from ..constants.states import DeviceCommands

logger = logger.bind(component=f"{__name__}")
# Максимальное количество строк на одной странице
ROWS_PER_PAGE = 20

def register_handlers(router: Router):
    @router.callback_query(F.data.startswith("page_"))
    async def pagination_callback(callback: CallbackQuery, state: FSMContext):
        """Обработчик для пагинации с использованием callback."""
        page = int(callback.data.split("_")[1])
        data = await state.get_data()
        total_pages = data.get('total_pages', 1)
        host = data.get('host')
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state_info = (
            f"P.S. Состояния: {Symbols.INTERFACE_OPER_UP.value} - Линк есть, {Symbols.INTERFACE_OPER_DOWN.value} - Линка нет, "
            f"{Symbols.INTERFACE_ADMIN_DOWN.value} - Порт выключен, {Symbols.STATUS_ERROR.value} - Неизвестно"
        )

        # Обновляем текущую страницу и отправляем новую страницу
        await state.update_data(page=page)
        await send_page(callback.message, state, page, total_pages, host, current_date, state_info)
        await callback.answer()

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
        display_data = {"text": full_message, "reply_markup": pagination_keyboard}
        await StateManager.set_state_with_previous(state, DeviceCommands.PORT_INFORMATION, display_data)

        await message.reply(text=full_message, reply_markup=pagination_keyboard, parse_mode="HTML")
