from aiogram import types, Dispatcher

from config import Config


async def mass_incident_handler(message: types.Message):
    incident_info = "Массовый инцидент обнаружен"
    await message.bot.send_message(Config.ADMIN_CHAT_ID, incident_info)

def register(dp: Dispatcher):
    dp.register_message_handler(mass_incident_handler, commands=["incident"])
