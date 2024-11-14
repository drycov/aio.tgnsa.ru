import datetime
import json
from typing import Any, Dict

from app.constants import LogMessages, NetworkMessages
from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from .snmp_functions import SNMPFunctions


class DeviceModelFilter:
    # Загрузка объединенного словаря с конфигурациями устройств
    device_data = HelperFunctions.load_device_data()

    @staticmethod
    def filter_device_model(dirty_data: str) -> str:
        """
        Определяет модель устройства на основе строки `dirty_data`.
        """
        app_logger.debug(f"Фильтрация модели устройства для данных: {dirty_data}")

        for model_key, model_info in DeviceModelFilter.device_data.items():
            if model_key in dirty_data:
                model_name = model_info["name"]
                app_logger.info(LogMessages.MODEL_FILTERED.value.format(model_name=model_name, model_key=model_key))
                return model_name

        app_logger.warning(LogMessages.MODEL_NOT_FOUND.value.format(dirty_data=dirty_data))
        return dirty_data

    @staticmethod
    def get_interface_config(model_key: str) -> Dict[str, Any]:
        """
        Возвращает интерфейсную конфигурацию на основе модели устройства.
        """
        model_info = DeviceModelFilter.device_data.get(model_key)
        if not model_info:
            app_logger.warning(LogMessages.CONFIG_NOT_FOUND.value.format(model_key=model_key))
            return {
                "interfaceRange": "auto",
                "interfaceList": "auto",
                "ddm": False,
                "adsl": False,
                "fibers": 0
            }

        # Загрузка интерфейсных данных для конфигурации модели
        interface_key = model_info.get("interface_key")
        interface_list_key = model_info.get("interface_list_key")
        return {
            "interfaceRange": HelperFunctions.load_interface_data(interface_key,
                                                                  "interfaceRange") if interface_key else "auto",
            "interfaceList": HelperFunctions.load_interface_data(interface_list_key,
                                                                 "interfaceList") if interface_list_key else "auto",
            "ddm": model_info.get("ddm", False),
            "adsl": model_info.get("adsl", False),
            "fibers": model_info.get("fibers", 0)
        }

    @staticmethod
    async def get_basic_info(host: str, community: str) -> Any | None:
        joid = HelperFunctions.load_oids()

        """
        Получает базовую информацию об устройстве через SNMP.
        """
        action = "get_basic_info"
        current_date = datetime.datetime.now().isoformat()

        app_logger.info(json.dumps({
            "date": current_date,
            "action": action,
            "host": host
        }))

        try:
            oid_model = joid["basic_oids"]["oid_model"]
            oid_sysname = joid["basic_oids"]["oid_sysname"]
            oid_uptime = joid["basic_oids"]["oid_uptime"]

            # Получение данных по OID
            dirty_data = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(host, oid_model, community),
                                                   encoding='iso-8859-1')
            sw_sys_name = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(host, oid_sysname, community),
                                                    encoding='iso-8859-1')
            up_time = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(host, oid_uptime, community))

            # # Преобразование байтов в строку, если это нужно
            # if isinstance(dirty_data, bytes):
            #     dirty_data = dirty_data.decode('utf-8')
            # if isinstance(sw_sys_name, bytes):
            #     sw_sys_name = sw_sys_name.decode('utf-8')
            # if isinstance(up_time, bytes):
            #     up_time = up_time.decode('utf-8')

            # Фильтрация модели устройства
            sw_model = DeviceModelFilter.filter_device_model(dirty_data)
            # if isinstance(sw_model, bytes):
            #     sw_model = sw_model.decode('utf-8')

            # Фильтрация модели устройства и формирование uptime
            sw_up_time = HelperFunctions.seconds_to_str(up_time)
            return NetworkMessages.DEVICE_INFO.value.format(
                host=host,
                sw_sys_name=sw_sys_name,
                sw_model=sw_model,
                sw_up_time=sw_up_time,
                up_time=up_time
            )


        except Exception as e:
            # Проверка и декодирование байтов в строку, если необходимо
            error_data = {
                "date": current_date,
                "action": action,
                "host": host,
                "error": str(e)
            }
            # Преобразуем значения в error_data в строки, если они имеют тип bytes
            for key, value in error_data.items():
                if isinstance(value, bytes):
                    error_data[key] = value.decode('utf-8')
            # Сериализация в JSON с ensure_ascii=False
            error_message = json.dumps(error_data, ensure_ascii=False)
            app_logger.error(error_message)
            return None
