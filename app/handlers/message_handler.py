from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import MenuLabels
from app.constants.states import DeviceCommands
from app.utils import StateManager
from app.utils.logger_instance import app_logger

router = Router()

@router.message(F.text == MenuLabels.PORT_STATUS.value)
async def port_info_command(message: Message, state: FSMContext):
    display_data = {"text": "Получение информации о порте."}
    await StateManager.set_state_with_previous(state, DeviceCommands.PORT_INFORMATION, display_data)
    await message.answer(**display_data)



# Команда "Назад"
@router.message(F.text == MenuLabels.BACK.value)
async def back_command(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception as e:
        app_logger.warning(f"Ошибка удаления сообщения: {e}")

    # Возвращаемся к предыдущему состоянию, используя сохраненные данные

