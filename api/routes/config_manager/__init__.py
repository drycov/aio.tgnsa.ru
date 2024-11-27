import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from api.services.config_service import ConfigService

ConfigManager = APIRouter()


class ConfigManagerAPI:
    """
    Класс для управления конфигурацией через API.
    """

    @staticmethod
    @ConfigManager.get("/config/")
    async def get_config():
        """
        Возвращает текущую конфигурацию.
        """
        from config import Config  # Динамический импорт, чтобы получить актуальные данные
        config_dict = {attr: getattr(Config, attr) for attr in dir(Config) if not attr.startswith("__")}
        return config_dict

    @staticmethod
    @ConfigManager.post("/config/")
    async def update_config(key: str, value: str):
        """
        Обновляет параметр конфигурации.
        """
        from config import Config  # Динамический импорт, чтобы работать с актуальными настройками

        if hasattr(Config, key):
            setattr(Config, key, value)
            os.environ[key] = value  # Обновление переменной окружения
            return {"message": f"Параметр {key} обновлён на {value}"}
        raise HTTPException(status_code=404, detail=f"Параметр {key} не найден.")

    @staticmethod
    @ConfigManager.get("/config/{key}")
    async def get_config_value(key: str):
        """
        Возвращает значение конкретного параметра конфигурации.
        """
        from config import Config

        if hasattr(Config, key):
            return {key: getattr(Config, key)}
        raise HTTPException(status_code=404, detail=f"Параметр {key} не найден.")

    @ConfigManager.post("/config/export")
    async def export_config(format: Literal["json", "csv", "sql", "env"] = "env"):
        """
        Экспортирует текущие настройки в файл .env.
        """
        exported_file = None
        try:
            file_name = f"config_export.{format}"
            file_path = Path(config.basedir / file_name)
            if format == 'env':
                file_path = config.config_env_path
                ConfigService.export_to_env(file_path, config.Config)
            elif format == "json":
                exported_file = ConfigService.export_to_json(file_path, config.Config)
            elif format == "csv":
                exported_file = ConfigService.export_to_csv(file_path, config.Config)
            elif format == "sql":
                exported_file = ConfigService.export_to_sql(file_path, config.Config)
            else:
                raise HTTPException(status_code=400, detail="Неподдерживаемый формат экспорта")
            return {"message": f"Конфигурация успешно экспортирована в {exported_file}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка экспорта конфигурации: {str(e)}")

    @ConfigManager.post("/config/import")
    async def import_config(format: Literal["json", "csv", "sql", "env"] = "env"):
        """
        Импортирует конфигурацию из файла.
        """
        file_path = None

    @ConfigManager.post("/config/update")
    async def update_env_variable(key: str, value: str):
        """
        Обновляет конкретную переменную окружения в .env.
        """
        file_path = config.config_env_path

        try:
            ConfigService.update_env_variable(file_path, key, value)
            return {"message": f"Переменная {key} успешно обновлена в {file_path}"}
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Файл {file_path} не найден.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка обновления переменной: {str(e)}")


class UpdateConfigRequest(BaseModel):
    key: str
    value: str
