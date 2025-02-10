import asyncio
import json
import traceback
from typing import Any, List

from puresnmp import Client, V2C, PyWrapper
from puresnmp.exc import Timeout

from config import Config
from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from ..constants import LogMessages


class SNMPFunctions:

    @staticmethod
    async def get_single_oid(host: str, oid: str, community: str, timeout: int = 6) -> Any:
        action = f"{__name__}.get_single_oid"
        current_date = HelperFunctions.get_current_date()
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
            return None
        try:
            client = PyWrapper(Client(host, V2C(community)))
            result = await client.get(oid)
            return result
        except Timeout:
            app_logger.warning(f"Пропуск хоста {host}: превышено время ожидания ({timeout} секунд).")
            return None
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return None

    @staticmethod
    async def check_snmp(
            host: str,
            communities: List[str],
            default_community: str = "public",
            timeout: float = 3.0
    ) -> str:
        """
        Асинхронная проверка SNMP community с расширенной обработкой ошибок.
        """
        action = f"{__name__}.check_snmp"

        try:
            joid = HelperFunctions.load_oids()
            if "basic_oids" not in joid:
                raise KeyError("Ключ 'basic_oids' отсутствует в файле oid.json.")

            sysObjectID = joid["basic_oids"]["oid_sysObjectID"]

            for community in communities:
                try:
                    result = await asyncio.wait_for(
                        SNMPFunctions.get_single_oid(host, sysObjectID, community),
                        timeout=timeout
                    )

                    if result:
                        return community

                except asyncio.TimeoutError:
                    app_logger.warning(f"Timeout для community {community} на хосте {host}")
                except Exception as e:
                    try:
                        # Передаем именно объект исключения
                        HelperFunctions.log_error(
                            action=action,
                            host=host,
                            error=e  # Объект исключения, а не строка
                        )
                    except Exception as log_error:
                        app_logger.error(f"Ошибка логирования: {log_error}")

        except Exception as global_error:
            app_logger.error(f"Критическая ошибка проверки SNMP: {global_error}")

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
            return []
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
            HelperFunctions.log_error(action=action, host=host, error=e)
            return None
