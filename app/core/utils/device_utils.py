import inspect
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import structlog
from app.bot.constants.symbols import Symbols
from app.core.oid_loader import OIDLoader
from app.core.utils.enr_parser import EnterpriseNumberRegistry
from app.core.utils.interface_processor import InterfaceProcessor
from app.core.utils.snmp_utils import SNMPUtils
from app.core.utils.utils import (
    parse_location,
    parse_snmp_uptime,
    seconds_to_str,
    to_string,
)

from app.core.logging_setup import logger
from app.core.utils.decorators import log_execution
from app.core.utils.device_matcher import ModelMatcher
from app.core.config import DATA_DIR, settings

logger = logger.bind(component="DeviceUtils")

DEVICE_MODEL_RULES = DATA_DIR / "device_models.toml"
MODEL_MATCHER = ModelMatcher(DEVICE_MODEL_RULES)


class DeviceUtils:
    """Утилиты для работы с сетевыми устройствами."""

    _model_matcher: Optional[ModelMatcher] = None

    @staticmethod
    async def get_ifDescr(host: str, community: str) -> List[str]:
        oids = OIDLoader.load()
        ifDescr_oid = oids["generic"]["interfaces"]["ifDescr"]
        result = await SNMPUtils.walk_snmp_data(host, community, ifDescr_oid)
        if not result:
            logger.warning("get_interface_range", host=host, error="No data received")
            return []
        return [
            v.decode("utf-8") if isinstance(v, bytes) else str(v)
            for v in result.values()
        ]

    @staticmethod
    async def get_ifIndex(host: str, community: str) -> List[int]:
        oids = OIDLoader.load()
        ifIndex_oid = oids["generic"]["interfaces"]["ifIndex"]
        result = await SNMPUtils.walk_snmp_data(host, community, ifIndex_oid)
        if not result:
            logger.warning("get_if_index_range", host=host, error="No data received")
            return []
        return [int(v) for v in result.values()]

    @staticmethod
    @log_execution(level="info")
    async def get_basic_info(host: str, community: str) -> Optional[Dict[str, Any]]:
        oids = OIDLoader.load()
        basic_oids = oids["generic"]["system"]

        # Параллельный запрос всех необходимых OID
        results = await SNMPUtils.bulk_get_snmp_data(
            host,
            community,
            [
                basic_oids["model"],
                basic_oids["sysName"],
                basic_oids["uptime"],
                basic_oids["sysLocation"],
                basic_oids["sysObjectID"],
            ],
        )

        if not results or len(results) != 5:
            logger.error(
                "get_basic_info: host=%s, error=%s, results=%s",
                host,
                "SNMP response is None or incomplete",
                results,
            )
            return None
        logger.info(f"{basic_oids["model"]}")
        # dirty_data, sw_sys_name, up_time, sys_location, sw_pen = results
        dirty_data = results.get(basic_oids["model"])
        sw_sys_name = results.get(basic_oids["sysName"])
        up_time = results.get(basic_oids["uptime"])
        sys_location = results.get(basic_oids["sysLocation"])
        sw_pen = results.get(basic_oids["sysObjectID"])

        logger.info(f"{dirty_data} {results}")

        if not all([dirty_data, sw_sys_name]):
            logger.error(
                "get_basic_info", host=host, error="Missing critical SNMP data"
            )
            return None

        dirty_data = to_string(dirty_data)
        sw_sys_name = to_string(sw_sys_name)
        # up_time = int(up_time) if up_time else 0

        parsed_oid = EnterpriseNumberRegistry.parse_oid(sw_pen)
        vendor = await EnterpriseNumberRegistry.search_pen_cached(parsed_oid["pen"])

        result_location = parse_location(sys_location)
        address = (
            f"{result_location.get('country', 'Неизвестная страна')}, "
            f"{result_location.get('city', 'Неизвестный город')}, "
            f"{result_location.get('street', 'Неизвестная улица')}, "
            f"{result_location.get('house_number', '0')}"
            if result_location
            else "Неизвестный адрес"
        )

        sw_model = DeviceUtils.filter_device_model(dirty_data)
        device_data = DeviceUtils.get_interface_config(dirty_data)
        sw_up_time = parse_snmp_uptime(up_time)

        return {
            "host": host,
            "vendor": vendor[0].organization if vendor else "Неизвестный вендор",
            "sw_sys_name": sw_sys_name,
            "sw_model": sw_model,
            "sw_up_time": sw_up_time,
            "up_time": up_time,
            "device_data": device_data,
            "address": address,
            "latitude": result_location.get("latitude", 0.0),
            "longitude": result_location.get("longitude", 0.0),
        }

    @classmethod
    def init_model_matcher(cls, rules_path: Path):
        if not rules_path.exists():
            logger.warning(
                "init_model_matcher", path=str(rules_path), error="File not found"
            )
            return
        cls._model_matcher = ModelMatcher(rules_path)
        logger.info("init_model_matcher: Initialized, path=%s", str(rules_path))

    @staticmethod
    def filter_device_model(raw_data: str) -> str:
        clean_data = to_string(raw_data, encoding="iso-8859-1")
        if not clean_data:
            return "Неизвестная модель"

        if DeviceUtils._model_matcher:
            matched = DeviceUtils._model_matcher.match(clean_data)
            if matched != clean_data:
                return matched

        logger.warning("filter_device_model: Fallback used. Raw data: %s", clean_data)
        return clean_data

    @staticmethod
    async def get_ifTypes(host: str, community: str) -> Dict[int, int]:
        """
        Возвращает словарь: { ifIndex: ifTypeCode }
        """
        oids = OIDLoader.load()
        ifType_oid = oids["generic"]["interfaces"]["ifType"]
        raw = await SNMPUtils.walk_snmp_data(host, community, ifType_oid)
        return {int(k.split(".")[-1]): int(v) for k, v in raw.items()}

    @staticmethod
    def get_interface_config(data: str) -> dict:
        # TODO: Реализовать при необходимости
        return {}

    @staticmethod
    async def get_port_status(
        host: str,
        port_if_list: List[str],
        port_if_range: List[str],
        community: str,
        model: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Получение статуса портов устройства по SNMP.

        :param host: IP-адрес устройства
        :param port_if_list: Список индексов SNMP (ifIndex) портов
        :param port_if_range: Список "человекочитаемых" названий портов (если есть)
        :param community: SNMP community string
        :param model: Название модели устройства
        :return: Список словарей с описанием каждого порта
        """
        results = []
        try:
            oids = OIDLoader.load()

            def get_descr_oid(
                model: Optional[str], joid: dict, ignore: bool = False
            ) -> str:
                target_models = ["IES-612", "IES1248-51", "SAM1008"]
                if not ignore:
                    if isinstance(model, str) and any(
                        sub in model for sub in target_models
                    ):
                        return joid["aam1212"]["ports"]["portName"]
                return joid["generic"]["interfaces"]["descrPorts"]

            descr_oid = get_descr_oid(model, oids, True)
            # logger.info(f"{descr_oid}")

            if not isinstance(port_if_list, list):
                logger.error(
                    f"[{inspect.currentframe().f_code.co_name}] port_if_list должен быть списком, но получил тип {type(port_if_list)}"
                )
                return []

            if not isinstance(port_if_range, list):
                logger.error(
                    f"[{inspect.currentframe().f_code.co_name}] port_if_range должен быть списком, но получил тип {type(port_if_range)}"
                )
                return []

            if len(port_if_list) != len(port_if_range):
                logger.warning(
                    f"[{inspect.currentframe().f_code.co_name}] Длина списков не совпадает: ifList={len(port_if_list)}, range={len(port_if_range)}"
                )

            s_ifaces = InterfaceProcessor.merge_and_sort_interfaces(
                port_if_range, port_if_list, True
            )
            port_if_range = InterfaceProcessor.extract_physical_ids(s_ifaces)
            port_if_list = InterfaceProcessor.extract_physical_ifNames(s_ifaces)

            for i, if_index in enumerate(port_if_range):
                try:
                    port_str = str(if_index)
                    # Проверяем, не вышли ли за границы списка
                    if i >= len(port_if_range):
                        port_if_range.append("")  # Добавляем пустое значение

                    # Обрабатываем D-Link, только если индекс в пределах списка
                    if (
                        i < len(port_if_list)
                        and isinstance(port_if_list[i], str)
                        and "D-Link" in port_if_list[i]
                    ):
                        port_if_list[i] = (
                            port_if_list[i].split()[1]
                            if "Port" in port_if_list[i]
                            else port_if_list[i]
                        )
                    descr_oid_full = f"{descr_oid}.{port_str}"

                    raw_descr = await SNMPUtils.get_snmp_data(
                        host, community, descr_oid_full
                    )
                    decoded_descr = to_string(raw_descr, encoding="iso-8859-1")

                    # Получение статуса интерфейса и ошибок
                    int_descr = to_string(
                        await SNMPUtils.get_snmp_data(host, community, descr_oid_full),
                        encoding="iso-8859-1",
                    )
                    port_oper_status = to_string(
                        await SNMPUtils.get_snmp_data(
                            host,
                            community,
                            f"{oids["generic"]["interfaces"]["operStatus"]}.{port_str}",
                        ),
                        encoding="iso-8859-1",
                    )

                    port_admin_status = to_string(
                        await SNMPUtils.get_snmp_data(
                            host,
                            community,
                            f"{oids["generic"]["interfaces"]["adminStatus"]}.{port_str}",
                        ),
                        encoding="iso-8859-1",
                    )
                    get_in_errors = await SNMPUtils.get_snmp_data(
                        host,
                        community,
                        f"{oids["generic"]["interfaces"]["inErrors"]}.{port_str}",
                    )

                    def clean_snmp_data(data: str, default: str = " ") -> str:
                        invalid_values = ["noSuchInstance", "noSuchObject", "0"]
                        return data if data not in invalid_values else default

                    int_descr = clean_snmp_data(int_descr)
                    int_errors = clean_snmp_data(get_in_errors)
                    int_name = port_if_list[i]

                    if "Huawei" in port_if_list[i]:
                        int_name = to_string(
                            await SNMPUtils.get_snmp_data(
                                host,
                                community,
                                f"{oids["linux"]["interfaces"]["ifName"]}.{port_str}",
                            ),
                            encoding="iso-8859-1",
                        )

                    results.append(
                        {
                            "index": port_str,
                            "label": int_name,
                            "description": decoded_descr,
                            "oper_status": port_oper_status,
                            "admin_status": port_admin_status,
                            "int_errors": int_errors,
                        }
                    )
                except Exception as inner_e:
                    logger.warning(
                        f"[{inspect.currentframe().f_code.co_name}] Ошибка при обработке порта {if_index}: {inner_e}"
                    )

            return results

        except Exception as e:
            logger.error(
                f"[{inspect.currentframe().f_code.co_name}] Критическая ошибка: {e}"
            )
            return []
