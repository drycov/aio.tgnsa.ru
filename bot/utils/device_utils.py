from typing import Any, Dict

from bot.constants import LogMessages
from bot.utils.helper_functions import HelperFunctions
from bot.utils.logger import logger


class DeviceModelFilter:
    # Загружаем объединенный словарь с конфигурациями
    device_data = HelperFunctions.load_device_data()

    @staticmethod
    def filter_device_model(dirty_data: str) -> str:
        """
        Определяет модель устройства на основе строки `dirty_data`.
        """
        logger.debug(f"Фильтрация модели устройства для данных: {dirty_data}")
        for model_key, model_info in DeviceModelFilter.device_data.items():
            if model_key in dirty_data:
                logger.info(LogMessages.MODEL_FILTERED.value.format(model_name=model_info["name"], model_key=model_key))
                return model_info["name"]
        logger.warning(LogMessages.MODEL_NOT_FOUND.value.format(dirty_data=dirty_data))
        return dirty_data

    @staticmethod
    def get_interface_config(model_key: str) -> Dict[str, Any]:
        """
        Возвращает интерфейсную конфигурацию на основе модели устройства.
        """
        model_info = DeviceModelFilter.device_data.get(model_key)
        if model_info:
            interface_key = model_info.get("interface_key")
            interface_list_key = model_info.get("interface_list_key")
            config = {
                "interfaceRange": HelperFunctions.load_interface_data(interface_key,
                                                                      "interfaceRange") if interface_key else "auto",
                "interfaceList": HelperFunctions.load_interface_data(interface_list_key,
                                                                     "interfaceList") if interface_list_key else "auto",
                "ddm": model_info.get("ddm", False),
                "adsl": model_info.get("adsl", False),
                "fibers": model_info.get("fibers", 0)
            }
            # logger.info(f"Конфигурация для модели '{model_key}' успешно получена.")
            return config
        else:
            logger.warning(LogMessages.CONFIG_NOT_FOUND.value.format(model_key=model_key))
            return {
                "interfaceRange": "auto",
                "interfaceList": "auto",
                "ddm": False,
                "adsl": False,
                "fibers": 0
            }
