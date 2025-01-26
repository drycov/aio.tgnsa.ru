

from aiogram import F, Router

from bot.constants.menu_labels import MenuLabels
from bot.constants.regexp import RegExpUtils
from aiogram.types.message import Message
from aiogram.fsm.context import FSMContext

from bot.constants.states import ERTMManager
from bot.utils.state_manager import StateManager


router = Router()
regexp = RegExpUtils()

@router.message(F.text == MenuLabels.ERTM_LIST_EQUIPMENT.value)
async def advanced_menu_command(message: Message, state: FSMContext):
    display_data = {"text": MenuLabels.ERTM_LIST_EQUIPMENT.value}
    await StateManager.set_state_with_previous(state, ERTMManager.ERTM_MENU, display_data)
    await message.answer(**display_data)
