import json
import inspect
from typing import Dict, Optional
from pathlib import Path
from pysnmp.hlapi.v3arch.asyncio import *
from app.core.config import logger
from app.core.patchs import BASE_DIR

logger = logger.bind(component="SNMPUtils")


class SNMPUtils:
    CACHE_DIR = BASE_DIR / "data/snmp_cache"  # Или куда удобно

    @staticmethod
    def format_oid(oid: str) -> str:
        if not oid.startswith("."):
            oid = "." + oid + "."
        return oid

    @staticmethod
    def parse_snmp_response(response: str) -> str:
        if response.startswith("SNMPv2-SMI::"):
            return response.split("::")[-1].strip()
        return response.strip()

    @staticmethod
    def format_snmp_error(error: str) -> str:
        return f"⚠️ <b>SNMP ошибка:</b> {error}"

    @staticmethod
    async def get_snmp_data(target_ip: str, community: str, oid: str) -> Optional[str]:
        oid = SNMPUtils.format_oid(oid)
        engine = SnmpEngine()

        if any(int(part) < 0 for part in oid.split(".") if part.isdigit()):
            logger.error(
                f"[{inspect.currentframe().f_code.co_name}] Недопустимый OID: {oid}"
            )
            return None

        try:
            result = await get_cmd(
                engine,
                CommunityData(community, mpModel=0),
                await UdpTransportTarget.create((target_ip, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
            errorIndication, errorStatus, errorIndex, varBinds = result

            if errorIndication:
                logger.error(f"SNMP error: {errorIndication}")
                return None
            elif errorStatus:
                logger.error(f"SNMP error: {errorStatus.prettyPrint()}")
                return None

            for varBind in varBinds:
                return SNMPUtils.parse_snmp_response(str(varBind[1]))
        except Exception as e:
            logger.exception(
                f"[{inspect.currentframe().f_code.co_name}] Ошибка SNMP GET: {e}"
            )
            return None

    @staticmethod
    async def walk_snmp_data(
        target_ip: str, community: str, oid: str, persist: bool = True
    ) -> Optional[Dict[str, str]]:
        """Асинхронно выполняет SNMP WALK до окончания ветки OID и сохраняет в JSON."""
        oid = SNMPUtils.format_oid(oid)
        result = {}
        engine = SnmpEngine()

        try:
            transport = await UdpTransportTarget.create((target_ip, 161))
            async for errorIndication, errorStatus, errorIndex, varBinds in walk_cmd(
                engine,
                CommunityData(community, mpModel=0),
                transport,
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            ):
                if errorIndication:
                    logger.error(f"SNMP error: {errorIndication}")
                    break
                elif errorStatus:
                    logger.error(
                        f"SNMP error: {errorStatus.prettyPrint()} at index {errorIndex}"
                    )
                    break

                for varBind in varBinds:
                    oid_str = str(varBind[0])
                    if not oid_str.startswith(oid.strip(".")):
                        # Вышли за пределы ветки
                        return result if result else None

                    value_str = SNMPUtils.parse_snmp_response(str(varBind[1]))
                    result[oid_str] = value_str

            return result if result else None

        except Exception as e:
            logger.exception(
                f"[{inspect.currentframe().f_code.co_name}] Ошибка SNMP WALK: {e}"
            )
            return None
