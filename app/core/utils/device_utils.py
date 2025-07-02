import inspect
from typing import List
from app.core.config import logger
from app.core.oid_loader import OIDLoader
from app.core.utils.enr_parser import EnterpriseNumberRegistry
from app.core.utils.snmp_utils import SNMPUtils
from app.core.utils.utils import parse_location, seconds_to_str, to_string

logger = logger.bind(component="DeviceUtils")


class DeviceUtils:
    """Утилиты для работы с устройствами в сети."""

    @staticmethod
    async def get_interface_range(host: str, community: str) -> List[str]:
        try:
            result = await SNMPUtils.walk_snmp_data(
                host, community, "1.3.6.1.2.1.2.2.1.2"
            )
            if not result:
                logger.warning(
                    f"[{inspect.currentframe().f_code.co_name}] Нет данных по интерфейсам от {host}"
                )
                return []

            # Просто str() от значений
            return [
                v.decode("utf-8") if isinstance(v, bytes) else str(v)
                for v in result.values()
            ]
        except Exception as e:
            logger.exception(
                f"[{inspect.currentframe().f_code.co_name}] Ошибка получения интерфейсов с {host}: {e}"
            )
            return []

    @staticmethod
    async def get_if_index_range(host: str, community: str) -> List[int]:
        try:
            result = await SNMPUtils.walk_snmp_data(
                host, community, "1.3.6.1.2.1.2.2.1.1"
            )
            if not result:
                logger.warning(
                    f"[{inspect.currentframe().f_code.co_name}] Нет данных по индексам интерфейсов от {host}"
                )
                return []

            return [int(v) for v in result.values()]
        except Exception as e:
            logger.exception(
                f"[{inspect.currentframe().f_code.co_name}] Ошибка получения индексов интерфейсов с {host}: {e}"
            )
            return []

    @staticmethod
    async def get_basic_info(host: str, community: str) -> dict | None:
        oids = OIDLoader.load()

        try:
            oid_model = oids["basic_oids"]["oid_model"]
            oid_sysname = oids["basic_oids"]["oid_sysname"]
            oid_uptime = oids["basic_oids"]["oid_uptime"]
            oid_sysLocation = oids["basic_oids"]["oid_sysLocation"]
            oid_sysObjectID = oids["basic_oids"]["oid_sysObjectID"]

            # Получение данных по OID
            try:
                dirty_data = await SNMPUtils.get_snmp_data(host, community, oid_model)
                print(dirty_data)
                if not dirty_data:
                    raise ValueError(
                        f"Не удалось получить данные по OID модели для хоста {host}"
                    )
                dirty_data = (
                    dirty_data.decode("utf-8")
                    if isinstance(dirty_data, bytes)
                    else str(dirty_data)
                )
            except Exception as e:
                logger.error(
                    f"Ошибка при получении данных OID модели для хоста {host}: {e}"
                )
                return None

            sw_sys_name = await SNMPUtils.get_snmp_data(host, community, oid_sysname)
            if not sw_sys_name:
                raise ValueError(f"Не удалось получить имя устройства для хоста {host}")
            sw_sys_name = (
                sw_sys_name.decode("utf-8")
                if isinstance(sw_sys_name, bytes)
                else str(sw_sys_name)
            )

            sw_pen = await SNMPUtils.get_snmp_data(host, community, oid_sysObjectID)
            up_time = await SNMPUtils.get_snmp_data(host, community, oid_uptime)
            sys_location = await SNMPUtils.get_snmp_data(
                host, community, oid_sysLocation
            )

            if not sw_pen or not up_time or not sys_location:
                raise ValueError(
                    f"Не удалось получить все необходимые данные для хоста {host}"
                )

            parsed_oid = EnterpriseNumberRegistry.parse_oid(sw_pen)
            vendor = EnterpriseNumberRegistry.search_pen(parsed_oid["pen"])
            logger.debug(vendor[0].organization)

            # Парсинг sys_location
            result = parse_location(sys_location)
            address = (
                (
                    f"{result.get('country', 'Неизвестная страна')}, "
                    f"{result.get('city', 'Неизвестный город')}, "
                    f"{result.get('street', 'Неизвестная улица')}, "
                    f"{result.get('house_number', '0')}"
                )
                if result
                else "Неизвестный адрес"
            )

            # Фильтрация модели устройства
            sw_model = DeviceUtils.filter_device_model(dirty_data)
            device_data = DeviceUtils.get_interface_config(dirty_data)

            # Фильтрация модели устройства и формирование uptime
            sw_up_time = seconds_to_str(up_time)

            return {
                "host": host,
                "vendor": vendor[0].organization,
                "sw_sys_name": sw_sys_name,
                "sw_model": sw_model,
                "sw_up_time": sw_up_time,
                "up_time": up_time,
                "device_data": device_data,
                "address": address,
                "latitude": result.get("latitude", 0.0) if result else 0.0,
                "longitude": result.get("longitude", 0.0) if result else 0.0,
            }

        except Exception as e:
            # Логирование ошибки с трассировкой
            logger.exception(
                f"[{inspect.currentframe().f_code.co_name}] Ошибка получения базовой информации с {host}: {e}"
            )
            return None

    @staticmethod
    def filter_device_model(dirty_data: str) -> str:
        """
        Определяет модель устройства на основе строки `dirty_data`.
        """
        dirty_data = to_string(dirty_data, encoding="iso-8859-1")
        for model_key, model_info in DeviceUtils.device_data.items():
            if model_key in dirty_data:
                model_name = model_info["name"]
                # app_logger.info(LogMessages.MODEL_FILTERED.value.format(model_name=model_name, model_key=model_key))
                return model_name

        logger.warning(
            f"[{inspect.currentframe().f_code.co_name}] Не удалось определить модель устройства из строки: {dirty_data}"
        )
        return dirty_data
