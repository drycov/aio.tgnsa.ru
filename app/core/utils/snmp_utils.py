import json
import inspect
from typing import Any, Dict, Optional
from pathlib import Path
from pysnmp.hlapi.v3arch.asyncio import *
from app.core.patchs import BASE_DIR



class SNMPUtils:
    from app.core.logging_setup import logger as _base_logger
    logger = _base_logger.bind(component="SNMPUtils")


    CACHE_DIR = BASE_DIR / "data/snmp_cache"  # Или куда удобно

    @staticmethod
    def format_oid(oid: str | list | Any) -> str:
        if isinstance(oid, list):
            # Преобразуем в строку, если список
            oid = ".".join(str(part).strip(".") for part in oid if part)
        elif not isinstance(oid, str):
            oid = str(oid)

        oid = oid.strip(".")  # Убираем лишние точки с начала и конца
        return f".{oid}."


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
            SNMPUtils.logger.error(
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
                SNMPUtils.logger.error(f"SNMP error: {errorIndication}")
                return None
            elif errorStatus:
                SNMPUtils.logger.error(f"SNMP error: {errorStatus.prettyPrint()}")
                return None

            for varBind in varBinds:
                return SNMPUtils.parse_snmp_response(str(varBind[1]))
        except Exception as e:
            SNMPUtils.logger.exception(
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
                    SNMPUtils.logger.error(f"SNMP error: {errorIndication}")
                    break
                elif errorStatus:
                    SNMPUtils.logger.error(
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
            SNMPUtils.logger.exception(
                f"[{inspect.currentframe().f_code.co_name}] Ошибка SNMP WALK: {e}"
            )
            return None

    @staticmethod
    async def bulk_get_snmp_data(
        target_ip: str,
        community: str,
        oids: list,
        timeout: int = 5,
        retry_count: int = 1
    ) -> Optional[Dict[str, str]]:
        """
        Асинхронно выполняет SNMP GET нескольких OID за один запрос.

        :param target_ip: IP-адрес целевого устройства
        :param community: SNMP community string
        :param oids: Список OID для запроса
        :param timeout: Таймаут соединения
        :param retry_count: Количество повторных попыток
        :return: Dict вида {oid: value}, или None при ошибке
        """
        engine = SnmpEngine()
        transport = await UdpTransportTarget.create((target_ip, 161), timeout=timeout, retries=retry_count)

        try:
            # Форматируем все OID и создаём объекты ObjectType
            object_types = [ObjectType(ObjectIdentity(SNMPUtils.format_oid(oid))) for oid in oids]

            result = await get_cmd(
                engine,
                CommunityData(community, mpModel=0),
                transport,
                ContextData(),
                *object_types
            )

            errorIndication, errorStatus, errorIndex, varBinds = result

            if errorIndication:
                SNMPUtils.logger.error("bulk_get_snmp_data", host=target_ip, error=str(errorIndication))
                return None
            elif errorStatus:
                SNMPUtils.logger.error(
                    "bulk_get_snmp_data",
                    host=target_ip,
                    error=f"{errorStatus.prettyPrint()} at {errorIndex}"
                )
                return None

            response = {}
            for varBind in varBinds:
                oid_str = str(varBind[0])
                value_str = SNMPUtils.parse_snmp_response(str(varBind[1]))
                response[oid_str] = value_str

            return response

        except Exception as e:
            SNMPUtils.logger.exception("bulk_get_snmp_data", host=target_ip, error=str(e))
            return None