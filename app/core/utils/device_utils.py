import inspect
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import structlog
from app.core.oid_loader import OIDLoader
from app.core.utils.enr_parser import EnterpriseNumberRegistry
from app.core.utils.snmp_utils import SNMPUtils
from app.core.utils.utils import parse_location, parse_snmp_uptime, seconds_to_str, to_string

from app.core.logging_setup import logger
from app.core.utils.decorators import log_execution
from app.core.utils.device_matcher import ModelMatcher
from app.core.config import DATA_DIR

logger = logger.bind(component="DeviceUtils")
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
logger = structlog.get_logger()

DEVICE_MODEL_RULES = DATA_DIR / "device_models.toml"
MODEL_MATCHER = ModelMatcher(DEVICE_MODEL_RULES)

class DeviceUtils:
    """Утилиты для работы с сетевыми устройствами."""
    _model_matcher: Optional[ModelMatcher] = None

    @staticmethod
    async def get_interface_range(host: str, community: str) -> List[str]:
        result = await SNMPUtils.walk_snmp_data(host, community, "1.3.6.1.2.1.2.2.1.2")
        if not result:
            logger.warning("get_interface_range", host=host, error="No data received")
            return []
        return [v.decode("utf-8") if isinstance(v, bytes) else str(v) for v in result.values()]

    @staticmethod
    async def get_if_index_range(host: str, community: str) -> List[int]:
        result = await SNMPUtils.walk_snmp_data(host, community, "1.3.6.1.2.1.2.2.1.1")
        if not result:
            logger.warning("get_if_index_range", host=host, error="No data received")
            return []
        return [int(v) for v in result.values()]

    @staticmethod
    @log_execution(level="info")
    async def get_basic_info(host: str, community: str) -> Optional[Dict[str, Any]]:
        oids = OIDLoader.load()
        basic_oids = oids["basic_oids"]

        # Параллельный запрос всех необходимых OID
        results = await SNMPUtils.bulk_get_snmp_data(
            host,
            community,
            [
                basic_oids["oid_model"],
                basic_oids["oid_sysname"],
                basic_oids["oid_uptime"],
                basic_oids["oid_sysLocation"],
                basic_oids["oid_sysObjectID"],
            ],
        )

        if not results or len(results) != 5:
            logger.error("get_basic_info: host=%s, error=%s, results=%s", host, "SNMP response is None or incomplete", results)
            return None

        # dirty_data, sw_sys_name, up_time, sys_location, sw_pen = results
        dirty_data = results.get(basic_oids["oid_model"])
        sw_sys_name = results.get(basic_oids["oid_sysname"])
        up_time = results.get(basic_oids["oid_uptime"])
        sys_location = results.get(basic_oids["oid_sysLocation"])
        sw_pen = results.get(basic_oids["oid_sysObjectID"])



        if not all([dirty_data, sw_sys_name]):
            logger.error("get_basic_info", host=host, error="Missing critical SNMP data")
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
            logger.warning("init_model_matcher", path=str(rules_path), error="File not found")
            return
        cls._model_matcher = ModelMatcher(rules_path)
        logger.info("init_model_matcher", path=str(rules_path), status="Initialized")

    @staticmethod
    def filter_device_model(raw_data: str) -> str:
        clean_data = to_string(raw_data, encoding="iso-8859-1")
        if not clean_data:
            return "Неизвестная модель"

        if DeviceUtils._model_matcher:
            matched = DeviceUtils._model_matcher.match(clean_data)
            if matched != clean_data:
                return matched

        logger.warning("filter_device_model", raw=clean_data, status="Fallback used")
        return clean_data

    @staticmethod
    def get_interface_config(data: str) -> dict:
        # TODO: Реализовать при необходимости
        return {}