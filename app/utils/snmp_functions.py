import json
import traceback
from typing import Any, List

from puresnmp import Client, V2C, PyWrapper

from config import Config
from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from ..bot_instance import SNMP_OID_SYSOBJECTID
from ..constants import LogMessages


# from pysnmp.hlapi.v3arch.asyncio import *


class SNMPFunctions:

    @staticmethod
    async def get_single_oid(host: str, oid: str, community: str) -> Any:
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
        except Exception as e:
            HelperFunctions.log_error(action, host, e)
            return None

    @staticmethod
    async def check_snmp(host: str, communities: List[str]) -> str:
        action = f"{__name__}.check_snmp"
        oid = SNMP_OID_SYSOBJECTID

        for community in communities:
            try:
                result = await SNMPFunctions.get_single_oid(host, oid, community)
                if result:
                    return community

            except Exception as e:
                HelperFunctions.log_error(action, host, e)
        return "public"  # Возврат значения по умолчанию, если все communities недоступны

    @staticmethod
    async def get_multi_oid(host: str, oid: str, community: str) -> list:
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
        except Exception as e:
            HelperFunctions.log_error(action, host, e)
            return []

    async def set_snmp_oid(host: str, oid: str, value: Any, community: str = None) -> Any:
        community = community or Config.SNMP_RW_COMMUNITIES
        action = f"{__name__}.set_snmp_oid"
        try:
            client = PyWrapper(Client(host, V2C(community)))
            result = await client.set(oid, value)
            return result
        except Exception as e:
            # Логирование ошибок
            HelperFunctions.log_error(action, host, e)
            return
