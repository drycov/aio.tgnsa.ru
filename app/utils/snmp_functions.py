import json
from typing import Any, List

from pysnmp.hlapi.v1arch.asyncio.slim import Slim
from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from ..bot_instance import SNMP_OID_SYSOBJECTID
from ..constants import LogMessages


# from pysnmp.hlapi.v3arch.asyncio import *


class SNMPFunctions:

    @staticmethod
    async def get_single_oid(host: str, oid: str, community: str) -> Any:
        action = LogMessages.GET_SINGLE_OID_ACTION.value
        current_date = HelperFunctions.get_current_date()
        try:
            # Используем Slim как контекстный менеджер для выполнения SNMP-запроса
            with Slim() as slim:
                error_indication, error_status, error_index, var_binds = await slim.get(
                    community,
                    host,
                    161,
                    ObjectType(ObjectIdentity(str(oid)))
                )

                if error_indication:
                    app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))
                    return None
                if error_status:
                    app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))
                    return None
                return var_binds[0][1]

        except Exception as e:
            error_data = {
                "date": current_date,
                "action": action,
                "host": host,
                "oid": oid,
                "error": str(e)
            }
            for key, value in error_data.items():
                if isinstance(value, bytes):
                    error_data[key] = value.decode('utf-8')
            app_logger.error(json.dumps(error_data, ensure_ascii=False))
            app_logger.error(LogMessages.ACTION_FAILED.value.format(action=action, host=host, oid=oid))
            return None

    # @staticmethod
    # def get_sync_single_oid(host: str, oid: str, community: str) -> Any:
    #     action = LogMessages.GET_SYNC_SINGLE_OID_ACTION.value
    #     try:
    #         iterator = getCmd(SnmpEngine(),
    #                           CommunityData(community),
    #                           UdpTransportTarget((host, 161)),
    #                           ContextData(),
    #                           ObjectType(ObjectIdentity(oid)),
    #                           timeout=5, retries=1)
    #         error_indication, error_status, error_index, var_binds = next(iterator)
    #
    #         if error_indication:
    #             app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))
    #             return None
    #         if error_status:
    #             app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))
    #             return None
    #
    #         return var_binds[0][1]
    #
    #     except Exception as e:
    #         app_logger.error(json.dumps({
    #             "date": HelperFunctions.get_current_date(),
    #             "action": action,
    #             "host": host,
    #             "oid": oid,
    #             "error": str(e)
    #         }))
    #         app_logger.error(LogMessages.ACTION_FAILED.value.format(action=action, host=host, oid=oid))
    #         return None

    @staticmethod
    async def check_snmp(host: str, communities: List[str]) -> str:
        action = LogMessages.CHECK_SNMP_ACTION.value
        oid = SNMP_OID_SYSOBJECTID

        for community in communities:
            print(f"Проверка community: {community}")
            try:
                result = await SNMPFunctions.get_single_oid(host, oid, community)
                if result:
                    print(f"SNMP доступен с community: {community}")
                    return community
                else:
                    print(f"SNMP недоступен с community: {community}")
            except Exception as e:
                app_logger.error(json.dumps({
                    "date": HelperFunctions.get_current_date(),
                    "action": action,
                    "host": host,
                    "community": community,
                    "error": str(e)
                }, ensure_ascii=False))
                print(f"Ошибка при проверке community '{community}': {e}")

        app_logger.info(LogMessages.SNMP_UNAVAILABLE.value.format(action=action, host=host))
        return "public"  # Возврат значения по умолчанию, если все communities недоступны

    # @staticmethod
    # async def get_multi_oid(host: str, oid: str, community: str) -> list:
    #     action = LogMessages.GET_MULTI_OID_ACTION.value
    #     results = []
    #
    #     try:
    #         iterator = nextCmd(SnmpEngine(),
    #                            CommunityData(community),
    #                            UdpTransportTarget((host, 161)),
    #                            ContextData(),
    #                            ObjectType(ObjectIdentity(oid)),
    #                            timeout=5, lexicographicMode=False)
    #
    #         for error_indication, error_status, error_index, var_binds in iterator:
    #             if error_indication:
    #                 app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))
    #                 return []
    #             if error_status:
    #                 app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))
    #                 return []
    #
    #             results.extend([str(var_bind[1]) for var_bind in var_binds])
    #
    #         return results
    #
    #     except Exception as e:
    #         app_logger.error(json.dumps({
    #             "date": HelperFunctions.get_current_date(),
    #             "action": action,
    #             "host": host,
    #             "oid": oid,
    #             "error": str(e)
    #         }, ensure_ascii=False))
    #         app_logger.error(LogMessages.ACTION_FAILED.value.format(action=action, host=host, oid=oid))
    #         return []
    #
    # @staticmethod
    # async def set_snmp_oid(host: str, oid: str, value: Any, community: str = None) -> Any:
    #     community = community or Config.SNMP_RW_COMMUNITY
    #     action = LogMessages.SET_SNMP_OID_ACTION.value
    #
    #     try:
    #         iterator = setCmd(SnmpEngine(),
    #                           CommunityData(community),
    #                           UdpTransportTarget((host, 161)),
    #                           ContextData(),
    #                           ObjectType(ObjectIdentity(oid), Integer(value)),
    #                           timeout=5)
    #
    #         error_indication, error_status, error_index, var_binds = next(iterator)
    #
    #         if error_indication:
    #             app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))
    #             return None
    #         if error_status:
    #             app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))
    #             return None
    #
    #         return var_binds[0][1]
    #
    #     except Exception as e:
    #         app_logger.error(json.dumps({
    #             "date": HelperFunctions.get_current_date(),
    #             "action": action,
    #             "host": host,
    #             "oid": oid,
    #             "error": str(e)
    #         }, ensure_ascii=False))
    #         app_logger.error(LogMessages.ACTION_FAILED.value.format(action=action, host=host, oid=oid))
    #         return None
