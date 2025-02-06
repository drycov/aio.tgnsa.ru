import asyncio
from typing import List

from aiogram import exceptions
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api import API
from bot.bot_instance import bot
from config import Config

Index = APIRouter()
api_instance = API()
Index.dependency_overrides = {"api": lambda: api_instance}


class MessageRequest(BaseModel):
    user_id: int
    message: str


@Index.get("/")
async def index(api: API = Depends()):
    """
    Информация об API и проекте.
    """
    return {
        "project_name": Config.APP_NAME,
        "version": Config.VERSION,
        "description": "Это API предоставляет функциональность для управления пользователями, задачами и конфигурациями.",
        "support_mail": Config.SUPPORT_EMAIL,
        "admin_mail": Config.ADMIN_EMAIL,
        "license": "MIT",
        "license_url": "https://opensource.org/licenses/MIT",
        "repository": "https://github.com/drykov/aio.tgnsa.ru",
        "documentation": "http://127.0.0.1:8000/docs",  # Локальный адрес документации
        "routes":api.list_routes()
    }


@Index.post("/send_message")
async def send_message(request: MessageRequest):
    """
    Отправка текстового сообщения пользователю через Telegram Bot.
    """
    try:
        # Создаём задачу для отправки сообщения
        result = await asyncio.create_task(
            bot.send_message(chat_id=request.user_id, text=request.message, parse_mode="HTML"))
        return {"message": "Сообщение отправлено", "result": result}
    except exceptions.TelegramBadRequest as e:
        if "blocked" in str(e).lower():
            raise HTTPException(status_code=403, detail="Бот заблокирован пользователем")
        elif "chat not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Чат с пользователем не найден")
        else:
            raise HTTPException(status_code=500, detail=f"Ошибка Telegram API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Неизвестная ошибка: {e}")


@Index.post("/broadcast")
async def broadcast_message(user_ids: List[int], message: str):
    """
    Массовая рассылка текстовых сообщений через Telegram Bot.
    """
    errors = []
    tasks = []

    for user_id in user_ids:
        tasks.append(asyncio.create_task(bot.send_message(chat_id=user_id, text=message)))

    # Выполняем все задачи параллельно
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for user_id, result in zip(user_ids, results):
        if isinstance(result, Exception):
            errors.append({"user_id": user_id, "error": str(result)})

    if errors:
        return {
            "message": "Сообщения отправлены с ошибками",
            "errors": errors
        }
    return {"message": "Все сообщения успешно отправлены"}


@Index.post("/start_bot", response_model=None)
async def start_bot(api: API = Depends()):  # Зависимость передана через Depends
    """
    Запуск бота через эндпоинт.
    """
    try:
        await api.start_bot_task()
        return {"message": "Бот успешно запущен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска бота: {e}")


@Index.post("/stop_bot", response_model=None)
async def stop_bot(api: API = Depends()):  # Зависимость передана через Depends
    """
    Остановка бота через эндпоинт.
    """
    try:
        await api.stop_bot_task()
        return {"message": "Бот успешно остановлен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка остановки бота: {e}")


@Index.post("/restart_bot", response_model=None)
async def restart_bot(api: API = Depends()):  # Зависимость передана через Depends
    """
    Перезапуск бота через эндпоинт.
    """
    try:
        await api.restart_bot_task()
        return {"message": "Бот успешно перезапущен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка перезапуска бота: {e}")
