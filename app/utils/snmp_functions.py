import json
from typing import Any, List

from loguru import logger
from pyasn1.type.univ import Integer
from pysnmp.entity.engine import SnmpEngine
from pysnmp.hlapi.v3arch import CommunityData, UdpTransportTarget, ContextData, get_cmd as getCmd, set_cmd as setCmd, \
    next_cmd as nextCmd
from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from config import Config
from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from ..constants import LogMessages


class SNMPFunctions:

    @staticmethod
    async def get_single_oid(host: str, oid: str, community: str) -> Any:
        action = LogMessages.GET_SINGLE_OID_ACTION.value
        try:
            iterator = getCmd(SnmpEngine(),
                              CommunityData(community),
                              UdpTransportTarget((host, 161)),
                              ContextData(),
                              ObjectType(ObjectIdentity(oid)),
                              timeout=5, retries=1)
            error_indication, error_status, error_index, var_binds = next(iterator)

            if error_indication:
                logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))

                app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))
                return None
            if error_status:
                logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))

                app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))
                return None

            return var_binds[0][1]

        except Exception as e:
            app_logger.error(json.dumps({
                "date": HelperFunctions.get_current_date(),
                "action": action,
                "host": host,
                "oid": oid,
                "error": str(e)
            }))
            app_logger.error(LogMessages.ACTION_FAILED.value.format(action=action, host=host, oid=oid))
            return None

    @staticmethod
    def get_sync_single_oid(host: str, oid: str, community: str) -> Any:
        action = LogMessages.GET_SYNC_SINGLE_OID_ACTION.value
        try:
            iterator = getCmd(SnmpEngine(),
                              CommunityData(community),
                              UdpTransportTarget((host, 161)),
                              ContextData(),
                              ObjectType(ObjectIdentity(oid)),
                              timeout=5, retries=1)
            error_indication, error_status, error_index, var_binds = next(iterator)

            if error_indication:
                app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))
                return None
            if error_status:
                app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))
                return None

            return var_binds[0][1]

        except Exception as e:
            app_logger.error(json.dumps({
                "date": HelperFunctions.get_current_date(),
                "action": action,
                "host": host,
                "oid": oid,
                "error": str(e)
            }))
            app_logger.error(LogMessages.ACTION_FAILED.value.format(action=action, host=host, oid=oid))
            return None

    @staticmethod
    async def check_snmp(host: str, communities: List[str]) -> str:
        action = LogMessages.CHECK_SNMP_ACTION.value
        oid = Config.SNMP_OID_SYSOBJECTID

        for community in communities:
            result = await SNMPFunctions.get_single_oid(host, oid, community)
            if result:
                return community

        app_logger.info(LogMessages.SNMP_UNAVAILABLE.value.format(host=host))
        return "public"

    @staticmethod
    async def get_multi_oid(host: str, oid: str, community: str) -> list:
        action = LogMessages.GET_MULTI_OID_ACTION.value
        results = []

        try:
            iterator = nextCmd(SnmpEngine(),
                               CommunityData(community),
                               UdpTransportTarget((host, 161)),
                               ContextData(),
                               ObjectType(ObjectIdentity(oid)),
                               timeout=5, lexicographicMode=False)

            for error_indication, error_status, error_index, var_binds in iterator:
                if error_indication:
                    app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))
                    return []
                if error_status:
                    app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))
                    return []

                results.extend([str(var_bind[1]) for var_bind in var_binds])

            return results

        except Exception as e:
            app_logger.error(json.dumps({
                "date": HelperFunctions.get_current_date(),
                "action": action,
                "host": host,
                "oid": oid,
                "error": str(e)
            }))
            app_logger.error(LogMessages.ACTION_FAILED.value.format(action=action, host=host, oid=oid))
            return []

    @staticmethod
    async def set_snmp_oid(host: str, oid: str, value: Any, community: str = None) -> Any:
        community = community or Config.SNMP_RW_COMMUNITY
        action = LogMessages.SET_SNMP_OID_ACTION.value

        try:
            iterator = setCmd(SnmpEngine(),
                              CommunityData(community),
                              UdpTransportTarget((host, 161)),
                              ContextData(),
                              ObjectType(ObjectIdentity(oid), Integer(value)),
                              timeout=5)

            error_indication, error_status, error_index, var_binds = next(iterator)

            if error_indication:
                app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_indication))
                return None
            if error_status:
                app_logger.error(LogMessages.SNMP_ERROR.value.format(error=error_status.prettyPrint()))
                return None

            return var_binds[0][1]

        except Exception as e:
            app_logger.error(json.dumps({
                "date": HelperFunctions.get_current_date(),
                "action": action,
                "host": host,
                "oid": oid,
                "error": str(e)
            }))
            app_logger.error(LogMessages.ACTION_FAILED.value.format(action=action, host=host, oid=oid))
            return None
