import os
import platform
from datetime import datetime

import psutil
import pytz
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import debug_mode, logger, settings
from app.core.patchs import project_paths

# from app.core.logger import logger


router = APIRouter()

# Инициализация шаблонов
templates = Jinja2Templates(directory=str(project_paths.templates_dir))


# Добавляем кастомный фильтр для форматирования datetime
def datetime_filter(value: str, format: str = "%d.%m.%Y %H:%M:%S") -> str:
    """
    Фильтр для форматирования даты и времени.

    Args:
        value (str): Строка с датой и временем
        format (str): Формат вывода

    Returns:
        str: Отформатированная строка
    """
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value)
            return dt.strftime(format)
        return value.strftime(format)
    except Exception:
        return value


templates.env.filters["datetime"] = datetime_filter


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Возвращает HTML-страницу с информацией о системе.
    """
    environment = "development" if debug_mode else "production"
    tz = pytz.timezone(settings.misc.TIMEZONE)
    current_time = datetime.now(tz).strftime("%H:%M:%S")  # Форматируем время

    # Получаем системную информацию
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app.APP_NAME,
            "favicon_url": settings.app.favicon_url,
            "static_url": settings.app.static_url,
            "description": settings.app.DESCRIPTION,
            "version": settings.app.VERSION,
            "environment": environment,
            "timezone": settings.misc.TIMEZONE,
            "current_time": current_time,  # Передаем объект datetime
            "system_info": {
                "os": f"{platform.system()} {platform.release()}",
                "python_version": platform.python_version(),
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "disk_usage": f"{disk.percent}%",
                "processors": psutil.cpu_count(),
                "hostname": platform.node()
            },
        }
    )


@router.get("/api/system-info")
async def get_system_info():
    """Возвращает обновленную системную информацию."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        tz = pytz.timezone(settings.misc.TIMEZONE)
        current_time = datetime.now(tz).strftime(
            "%H:%M:%S")  # Форматируем время
        logger.debug(f"current_time: {current_time}")
        return {
            "status": "success",
            "data": {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "disk_usage": f"{disk.percent}%",
                "current_time": current_time
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
