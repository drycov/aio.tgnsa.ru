import inspect
from typing import Optional, List
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from app.core.config import logger
from pysnmp.hlapi.v1arch.asyncio import *

logger = logger.bind(component="SNMPCommunityScanner")


class SNMPCommunityScanner:
    def __init__(
        self,
        target_ip: str,
        communities: List[str],
        oid: str = "1.3.6.1.2.1.1.1.0",
        timeout: int = 1,
        retries: int = 1,
    ):
        self.target_ip = target_ip
        self.communities = communities
        self.oid = oid
        self.timeout = timeout
        self.retries = retries

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(TimeoutError),
        reraise=True,
    )
    async def _snmp_get(self, community: str) -> Optional[str]:
        """Выполняет SNMP GET запрос асинхронно."""
        logger.debug(
            f"[{inspect.currentframe().f_code.co_name}]Trying community '{community}'..."
        )

        with SnmpDispatcher() as snmpDispatcher:
            iterator = await get_cmd(
                snmpDispatcher,
                CommunityData(str(community), mpModel=0),
                await UdpTransportTarget.create((str(self.target_ip), 161)),
                ("1.3.6.1.2.1.1.1.0", None),
            )

            errorIndication, errorStatus, errorIndex, varBinds = iterator

            if errorIndication:
                logger.error(
                    f"[{inspect.currentframe().f_code.co_name}] SNMP error for community '{community}': {errorIndication}"
                )
                return None
            elif errorStatus:
                logger.error(
                    f"[{inspect.currentframe().f_code.co_name}] SNMP error for community '{community}': {errorStatus.prettyPrint()}"
                )
                return None
            else:
                for varBind in varBinds:
                    value = varBind
                    return str(value)

            return None

    async def find_valid_community(self) -> Optional[str]:
        """Поиск рабочей SNMP community строки."""
        for community in self.communities:
            try:
                result = await self._snmp_get(community)
                if result:
                    logger.info(
                        f"[{inspect.currentframe().f_code.co_name}] ✅ Valid community string found: '{community}'"
                    )
                    return community
            except TimeoutError as e:
                logger.warning(
                    f"[{inspect.currentframe().f_code.co_name}] Timeout for community '{community}': {e}"
                )
            except Exception as e:
                logger.error(
                    f"[{inspect.currentframe().f_code.co_name}] Unhandled error for community '{community}': {e}"
                )

        logger.warning(
            f"[{inspect.currentframe().f_code.co_name}] ❌ No valid community string found."
        )
        return None
