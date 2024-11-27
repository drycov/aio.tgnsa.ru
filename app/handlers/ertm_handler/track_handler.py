from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import MenuLabels, Messages, ERTMManager
from app.keyboards import ertm_track_location
from app.utils import StateManager
from ertm import ERTM

router = Router()


@router.message(F.text == MenuLabels.ERTM_TRACK_EQUIPMENT.value)
async def cidr_calc_command(message: Message, state: FSMContext):
    display_data = {"text": Messages.SEND_LOCATION.value}
    await StateManager.set_state_with_previous(state, ERTMManager.TRACK_EQ, display_data)
    await message.answer(**display_data, reply_markup=ertm_track_location)
    # await state.update_data(waiting_for_subnet=True)


@router.message(F.location, StateFilter(ERTMManager.TRACK_EQ))
async def handle_location(message: Message):
    user_location = [message.location.latitude, message.location.longitude]
    radius = 150  # Радиус в метрах

    # Найти устройства в радиусе
    nearby_devices = []
    ertm = ERTM()  # Создайте экземпляр класса
    devices = ertm.get_devices_from_db()  # Правильный вызов
    for device in devices:
        distance = ERTM.calculate_distance(user_location, device["coords"])
        if distance <= radius:
            nearby_devices.append(f"{device['name']} (расстояние: {int(distance)} м)")

    if nearby_devices:
        await message.answer(
            "Устройства рядом:\n" + "\n".join(nearby_devices)
        )
    else:
        await message.answer("В радиусе 50 метров нет устройств.")
