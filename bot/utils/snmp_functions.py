import json
import traceback
from typing import Any, List

from puresnmp import Client, V2C, PyWrapper
from puresnmp.exc import Timeout

from config import Config
from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from ..constants import LogMessages


# from pysnmp.hlapi.v3arch.asyncio import *


class SNMPFunctions:

    @staticmethod
    async def get_single_oid(host: str, oid: str, community: str, timeout: int = 6) -> Any:
        action = f"{__name__}.get_single_oid"
        current_date = HelperFunctions.get_current_date()
        # Проверка OID на наличие некорректных значений
        oid_parts = oid.split(".")
        if any(int(part) < 0 for part in oid_parts if part.isdigit()):
            error_data = {
                "date": current_date,
                "action": action,
                "host": host,
                "oid": oid,
                "error": "OID содержит отрицательные     значения, что недопустимо",
                "trace": traceback.format_exc()
            }
            app_logger.error(json.dumps(error_data, ensure_ascii=False))
            return None
        try:
            client = PyWrapper(Client(host, V2C(community)))
            result = await client.get(oid)
            return result
        except Timeout:
            app_logger.warning(f"Пропуск хоста {host}: превышено время ожидания ({timeout} секунд).")
            return None  # Пропускаем хост, если произошел тайм-аут
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return None

    @staticmethod
    async def check_snmp(host: str, communities: List[str], default_community: str = "public") -> str:
        """
        Проверяет доступность SNMP community string для устройства.

        Args:
            host (str): IP-адрес устройства.
            communities (List[str]): Список SNMP community strings для проверки.
            default_community (str): Значение по умолчанию, если ни один community string не прошёл.

        Returns:
            str: Первый доступный SNMP community string или значение по умолчанию.
        """
        action = f"{__name__}.check_snmp"
        joid = HelperFunctions.load_oids()
        # app_logger.info(f"Загруженные данные из oid.json: {joid}")
        if "basic_oids" not in joid:
            raise KeyError("Ключ 'basic_oids' отсутствует в файле oid.json.")
        sysObjectID = joid["basic_oids"]["oid_sysObjectID"]

        for community in communities:
            try:
                # Пробуем получить значение по OID с данным community string
                result = await SNMPFunctions.get_single_oid(host, sysObjectID, community)
                if result:
                    # Возврат community, если устройство отвечает
                    return community
            except Exception as e:
                # Логируем ошибку для текущего community string
                HelperFunctions.log_error(action=action, host=host, error=e)

        # Если ни один community string не подошёл, возвращаем значение по умолчанию
        return default_community

    @staticmethod
    async def get_multi_oid(host: str, oid: str, community: str, timeout: int = 6) -> list:
        action = LogMessages.GET_MULTI_OID_ACTION.value
        current_date = HelperFunctions.get_current_date()

        results = []
        oid_parts = oid.split(".")
        if any(int(part) < 0 for part in oid_parts if part.isdigit()):
            error_data = {
                "date": current_date,
                "action": action,
                "host": host,
                "oid": oid,
                "error": "OID содержит отрицательные значения, что недопустимо",
                "trace": traceback.format_exc()
            }
            app_logger.error(json.dumps(error_data, ensure_ascii=False))
            return []
        try:
            client = PyWrapper(Client(host, V2C(community)))
            result = client.walk(oid)
            async for row in result:
                results.append(row)
            return results
        except Timeout:
            app_logger.warning(f"Пропуск хоста {host}: превышено время ожидания ({timeout} секунд).")
            return []  # Пропускаем хост, если произошел тайм-аут
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return []

    @staticmethod
    async def set_snmp_oid(host: str, oid: str, value: Any, community: str = None) -> Any:
        community = community or Config.SNMP_RW_COMMUNITIES
        action = f"{__name__}.set_snmp_oid"
        try:
            client = PyWrapper(Client(host, V2C(community)))
            result = await client.set(oid, value)
            return result
        except Exception as e:
            # Логирование ошибок
            HelperFunctions.log_error(action=action, host=host, error=e)
            return
