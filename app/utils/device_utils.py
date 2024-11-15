import asyncio
import json
from typing import Any, Dict, List, Optional

from app.constants import LogMessages, Symbols, ErrorMessages
from config import Config
from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from .snmp_functions import SNMPFunctions

current_date = HelperFunctions.get_current_date()


class DeviceUtils:

    async def get_interface_range(host: str, community: str) -> List[str]:
        """
        Получает диапазон интерфейсов устройства с помощью SNMP.
        """
        # OID для имен интерфейсов. Обычно для интерфейсов используется .1.3.6.1.2.1.2.2.1.2 (ifDescr)
        action = f"{__name__}.get_interface_range"
        oid_ifDescr = '.1.3.6.1.2.1.2.2.1.2'
        try:
            task = asyncio.create_task(SNMPFunctions.get_multi_oid(host, oid_ifDescr, community))
            interface_names = HelperFunctions.to_string(await task)

            # Преобразование значений с учетом типа
            return [
                index[1].decode('utf-8') if isinstance(index[1], bytes) else str(index[1])
                for index in interface_names
            ]
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return []

    async def get_interface_list(host: str, community: str) -> List[int]:
        """
        Получает список идентификаторов интерфейсов устройства с помощью SNMP.
        """
        # OID для индексов интерфейсов: обычно .1.3.6.1.2.1.2.2.1.1 (ifIndex)
        action = f"{__name__}.get_interface_list"
        oid_ifIndex = '.1.3.6.1.2.1.2.2.1.1'
        try:
            task = asyncio.create_task(SNMPFunctions.get_multi_oid(host, oid_ifIndex, community))
            interface_indices = HelperFunctions.to_string(await task)
            return [int(index[1]) for index in interface_indices]
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return []

    async def process_vlan_entry(host: str, community: str, results=None):
        if results is None:
            results = []
        joid = HelperFunctions.load_oids()

        action = f"{__name__}.process_vlan_entry"
        oid_vlan_list = joid["basic_oids"]["oid_vlan_list"]
        oid_vlan_id = joid["basic_oids"]["oid_vlan_id"]
        try:
            vlan_name = await SNMPFunctions.get_multi_oid(host, oid_vlan_list, community)
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return

        try:
            vlan_id = await SNMPFunctions.get_multi_oid(host, oid_vlan_id, community)
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return

        if not vlan_name or not vlan_id:
            raise Exception(ErrorMessages.error_message(host))

            # Преобразуем списки PyVarBind в словари для удобства
        vlan_id_dict = {entry.oid.split('.')[-1]: entry.value for entry in vlan_id}
        vlan_name_dict = {
            entry.oid.split('.')[-1]: entry.value.decode('utf-8') if isinstance(entry.value, bytes) else entry.value
            for entry in vlan_name}

        for key, vlan_name in vlan_name_dict.items():
            vlan_id = vlan_id_dict.get(key)
            if vlan_id is not None:
                results.append([vlan_id, vlan_name])

    # Загрузка объединенного словаря с конфигурациями устройств
    device_data = HelperFunctions.load_device_data()

    @staticmethod
    def filter_device_model(dirty_data: str) -> str:
        """
        Определяет модель устройства на основе строки `dirty_data`.
        """
        dirty_data = HelperFunctions.to_string(dirty_data, encoding='iso-8859-1')
        for model_key, model_info in DeviceUtils.device_data.items():
            if model_key in dirty_data:
                model_name = model_info["name"]
                app_logger.info(LogMessages.MODEL_FILTERED.value.format(model_name=model_name, model_key=model_key))
                return model_name

        app_logger.warning(LogMessages.MODEL_NOT_FOUND.value.format(dirty_data=dirty_data))
        return dirty_data

    @staticmethod
    def get_interface_config(dirty_data: str) -> Dict[str, Any]:
        """
        Возвращает интерфейсную конфигурацию на основе модели устройства.
        """
        dirty_data = HelperFunctions.to_string(dirty_data, encoding='iso-8859-1')
        for model_key, model_info in DeviceUtils.device_data.items():
            if model_key in dirty_data:
                if not model_info:
                    app_logger.warning(LogMessages.CONFIG_NOT_FOUND.value.format(model_key=model_key))
                    return {
                        "interfaceRange": "auto",
                        "interfaceList": "auto",
                        "ddm": False,
                        "adsl": False,
                        "fibers": 0
                    }
                # Загрузка интерфейсных данных для конфигурации модели
                interface_key = model_info.get("interface_key")
                interface_list_key = model_info.get("interface_list_key")

                return {
                    "interfaceRange": HelperFunctions.load_interface_data(interface_key,
                                                                          "interfaceRange") if interface_key else "auto",
                    "interfaceList": HelperFunctions.load_interface_data(interface_list_key,
                                                                         "interfaceList") if interface_list_key else "auto",
                    "ddm": model_info.get("ddm", False),
                    "adsl": model_info.get("adsl", False),
                    "fibers": model_info.get("fibers", 0)
                }
        app_logger.warning(LogMessages.MODEL_NOT_FOUND.value.format(dirty_data=dirty_data))
        return {
            "interfaceRange": "auto",
            "interfaceList": "auto",
            "ddm": False,
            "adsl": False,
            "fibers": 0
        }

    @staticmethod
    async def get_port_status(
            host: str,
            port_if_list: List[str],
            port_if_range: List[str],
            community: str,
            model: Optional[str] = None,
    ):
        results = []
        action = f"{__name__}.get_port_status"
        joid = HelperFunctions.load_oids()
        # Определяем descr_oid в зависимости от модели
        descr_oid = (
            joid["AAM1212_oid"]["subrPortName"]
            if any(sub in model for sub in ["IES-612", "IES1248-51", "SAM1008"])
            else joid["basic_oids"]["oid_descr_ports"]
        )

        try:
            if port_if_list is None:
                port_if_list = []

            if port_if_range is None:
                port_if_range = []

            for i, port in enumerate(port_if_list):
                port_str = str(port)  # Преобразуем port в строку
                # Получение описания интерфейса
                test_int_descr = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(
                    host, descr_oid + port_str, community
                ), encoding='iso-8859-1')

                # Пропуск ненужных интерфейсов
                if not port_if_range[i].startswith("port") and not port_if_range[i].startswith("D-Link"):
                    if (
                            any(sub in port_if_range[i] for sub in Config.EXCLUDED_SUBSTRINGS)
                            or port_if_range[i].isdigit()
                            or any(bad_sub in port_if_range[i] for bad_sub in [
                        '.ServiceInstance', 'noSuchInstance', "E1", "AUX",
                        f"{test_int_descr}.", "Po", "ControlEthernet", "Port",
                        "802.1Q", "Logical-int", "rif", "stack-port", "loopback"
                    ])
                    ):
                        continue

                # Получение статуса интерфейса и ошибок
                int_descr = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(
                    host, descr_oid + port_str, community
                ), encoding='iso-8859-1')
                port_oper_status = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(
                    host, f"{joid['basic_oids']['oid_oper_ports']}{port_str}", community
                ), encoding='iso-8859-1')
                port_admin_status = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(
                    host, f"{joid['basic_oids']['oid_admin_ports']}{port_str}", community
                ), encoding='iso-8859-1')
                get_in_errors = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(
                    host, f"{joid['basic_oids']['oid_inerrors']}{port_str}", community
                ), encoding='iso-8859-1')

                # Обработка имен интерфейсов D-Link
                if "D-Link" in port_if_range[i]:
                    port_if_range[i] = port_if_range[i].split()[1] if "Port" in port_if_range[i] else port_if_range[i]

                # Определение статуса порта
                oper_status = {
                    1: Symbols.CABLE_OK.value,
                    2: Symbols.CABLE_CHECKED.value,
                }.get(port_oper_status, Symbols.CABLE_UNKNOWN.value)

                if port_admin_status == "2":
                    oper_status = Symbols.STATUS_ADMIN_DISABLED.value

                # Подготовка и нормализация данных
                fix_int_descr = int_descr if int_descr not in ["noSuchInstance", "noSuchObject"] else " "
                fix_in_errors = get_in_errors if get_in_errors not in ["noSuchInstance", "noSuchObject", "0"] else " "
                fix_int_name = port_if_range[i]

                if "Huawei" in port_if_range[i]:
                    fix_int_name = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(
                        host, f"{joid['linux_server']['oid_ifName']}.{port_str}", community
                    ), encoding='iso-8859-1')

                results.append([
                    fix_int_name,
                    oper_status,
                    fix_in_errors,
                    fix_int_descr
                ])

            return results

        except Exception as e:
            # Логирование ошибки
            HelperFunctions.log_error(action=action, host=host, error=e)

            return

    @staticmethod
    async def get_basic_info(host: str, community: str) -> Any | None:
        joid = HelperFunctions.load_oids()

        """
        Получает базовую информацию об устройстве через SNMP.
        """
        action = "get_basic_info"

        app_logger.info(json.dumps({
            "date": current_date,
            "action": action,
            "host": host
        }))

        try:
            oid_model = joid["basic_oids"]["oid_model"]
            oid_sysname = joid["basic_oids"]["oid_sysname"]
            oid_uptime = joid["basic_oids"]["oid_uptime"]

            # Получение данных по OID
            dirty_data = await SNMPFunctions.get_single_oid(host, oid_model, community),
            dirty_data = dirty_data[0].decode('utf-8')
            sw_sys_name = await SNMPFunctions.get_single_oid(host, oid_sysname, community),
            sw_sys_name = sw_sys_name[0].decode('utf-8')

            up_time = await SNMPFunctions.get_single_oid(host, oid_uptime, community)

            # Фильтрация модели устройства
            sw_model = DeviceUtils.filter_device_model(str(dirty_data))
            device_data = DeviceUtils.get_interface_config(str(dirty_data))
            # if isinstance(sw_model, bytes):
            #     sw_model = sw_model.decode('utf-8')

            # Фильтрация модели устройства и формирование uptime
            sw_up_time = HelperFunctions.seconds_to_str(up_time)
            return {
                "host": host,
                "sw_sys_name": sw_sys_name,
                "sw_model": sw_model,
                "sw_up_time": sw_up_time,
                "up_time": up_time,
                "device_data": device_data
            }



        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)

            return None

    @staticmethod
    async def get_vlan_list(host: str, community: str):
        results = []
        action = f"{__name__}.get_port_status"
        try:
            await DeviceUtils.process_vlan_entry(host, community, results)
            return results
            # return HelperFunctions.table_formatted_output(results, ["Vlan ID", "Vlan NAME"])
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return None
