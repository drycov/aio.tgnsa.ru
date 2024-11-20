from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import MenuLabels, Messages, ERTMManager
from app.keyboards import ertm_track_location
from app.utils import StateManager, ERTMUtils

router = Router()

devices = [
    {"name": "Device 1", "coords": [49.670784, 83.828939]},
    {"name": "Device 2", "coords": [49.670700, 83.828800]},
    {"name": "Device 3", "coords": [49.671000, 83.829000]},
    {"name": "Device 4", "coords": [49.675000, 83.830000]},  # Вне радиуса 50 м
]


@router.message(F.text == MenuLabels.ERTM_TRACK_EQUIPMENT.value)
async def cidr_calc_command(message: Message, state: FSMContext):
    display_data = {"text": Messages.ENTER_SUBNET.value}
    await StateManager.set_state_with_previous(state, ERTMManager.TRACK_EQ, display_data)
    await message.answer(**display_data, reply_markup=ertm_track_location)
    # await state.update_data(waiting_for_subnet=True)


@router.message(F.location)
async def handle_location(message: Message):
    user_location = [message.location.latitude, message.location.longitude]
    radius = 50  # Радиус в метрах

    # Найти устройства в радиусе
    nearby_devices = []
    for device in devices:
        distance = ERTMUtils.calculate_distance(user_location, device["coords"])
        if distance <= radius:
            nearby_devices.append(f"{device['name']} (расстояние: {int(distance)} м)")

    if nearby_devices:
        await message.answer(
            "Устройства рядом:\n" + "\n".join(nearby_devices)
        )
    else:
        await message.answer("В радиусе 50 метров нет устройств.")
