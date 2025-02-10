import asyncio
import json
import re
import traceback
from typing import Any, Dict, List, Optional, Callable
from puresnmp.varbind import PyVarBind
from bot.constants import LogMessages, Symbols, ErrorMessages
from config import Config
from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from .pen_finder import PENFinder
from .snmp_functions import SNMPFunctions
import numpy as np

current_date = HelperFunctions.get_current_date()


class DeviceUtils:
    # Загрузка объединенного словаря с конфигурациями устройств
    device_data = HelperFunctions.load_device_data()

    @staticmethod
    async def get_interface_range(host: str, community: str, oid_group="basic_oids", oid="oid_ifName") -> List[str]:
        """
        Получает диапазон интерфейсов устройства с помощью SNMP.
        """
        # OID для имен интерфейсов. Обычно для интерфейсов используется .1.3.6.1.2.1.2.2.1.2 (ifDescr)
        action = f"{__name__}.get_interface_range"
        joid = HelperFunctions.load_oids()       
        oid_ifDescr = joid[oid_group][oid]

        # oid_ifDescr = '.1.3.6.1.2.1.31.1.1.1.1'
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

    @staticmethod
    async def get_interface_list(host: str, community: str, oid_group="basic_oids", oid="oid_ifIndex") -> List[int]:
        """
        Получает список идентификаторов интерфейсов устройства с помощью SNMP.
        """
        # OID для индексов интерфейсов: обычно .1.3.6.1.2.1.2.2.1.1 (ifIndex)
        action = f"{__name__}.get_interface_list"
        joid = HelperFunctions.load_oids()       
        oid_ifIndex = joid[oid_group][oid]
        try:
            task = asyncio.create_task(SNMPFunctions.get_multi_oid(host, oid_ifIndex, community))
            interface_indices = HelperFunctions.to_string(await task)
            return [int(index[1]) for index in interface_indices]
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return []

    @staticmethod
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

    @staticmethod
    def filter_device_model(dirty_data: str) -> str:
        """
        Определяет модель устройства на основе строки `dirty_data`.
        """
        dirty_data = HelperFunctions.to_string(dirty_data, encoding='iso-8859-1')
        for model_key, model_info in DeviceUtils.device_data.items():
            if model_key in dirty_data:
                model_name = model_info["name"]
                # app_logger.info(LogMessages.MODEL_FILTERED.value.format(model_name=model_name, model_key=model_key))
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
                        "gpon:": False,
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
                    "gpon": model_info.get("gpon", False),
                    "fibers": model_info.get("fibers", 0)
                }
        app_logger.warning(LogMessages.MODEL_NOT_FOUND.value.format(dirty_data=dirty_data))
        return {
            "interfaceRange": "auto",
            "interfaceList": "auto",
            "ddm": False,
            "adsl": False,
            "gpon": False,
            "fibers": 0
        }

    @staticmethod
    async def get_port_status(
            host: str,
            port_if_list: List[str],
            port_if_range: List[str],
            community: str,
            model: Optional[str]=None,
    ):
        results = []
        action = f"{__name__}.get_port_status"
        joid = HelperFunctions.load_oids()

        # Определяем descr_oid в зависимости от модели
        def get_descr_oid(model: str, joid: dict) -> str:
            target_models = ["IES-612", "IES1248-51", "SAM1008"]
            return joid["AAM1212_oid"]["subrPortName"] if any(sub in model for sub in target_models) else joid["basic_oids"]["oid_descr_ports"]
        
        descr_oid = get_descr_oid(model, joid)

        try:
            if port_if_list is None:
                port_if_list = []

            if port_if_range is None:
                port_if_range = []

            # Логируем возможное расхождение в длине списков
            if len(port_if_list) != len(port_if_range):
                HelperFunctions.log_error(
                    action=action,
                    host=host,
                    error=Exception(f"Несоответствие размеров списков: port_if_list={len(port_if_list)}, port_if_range={len(port_if_range)}")
                )

            for i, port in enumerate(port_if_list):
                port_str = str(port)  # Преобразуем port в строку
                # Проверяем, не вышли ли за границы списка
                if i >= len(port_if_range):
                    port_if_range.append("")  # Добавляем пустое значение

                # Обрабатываем D-Link, только если индекс в пределах списка
                if i < len(port_if_range) and "D-Link" in port_if_range[i]:
                    port_if_range[i] = port_if_range[i].split()[1] if "Port" in port_if_range[i] else port_if_range[i]

            # Получение описания интерфейса
                test_int_descr = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(
                    host, descr_oid + port_str, community
                ), encoding='iso-8859-1')

                # Пропуск ненужных интерфейсов
                if i < len(port_if_range):
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
                def clean_snmp_data(data: str, default: str=" ") -> str:
                    invalid_values = ["noSuchInstance", "noSuchObject", "0"]
                    return data if data not in invalid_values else default

                fix_int_descr = clean_snmp_data(int_descr)
                fix_in_errors = clean_snmp_data(get_in_errors)
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
    async def get_basic_info(host: str, community: str) -> dict | None:
        joid = HelperFunctions.load_oids()

        action = "get_basic_info"
        current_date = HelperFunctions.get_current_date()

        app_logger.info(json.dumps({
            "date": current_date,
            "action": action,
            "host": host
        }))

        try:
            oid_model = joid["basic_oids"]["oid_model"]
            oid_sysname = joid["basic_oids"]["oid_sysname"]
            oid_uptime = joid["basic_oids"]["oid_uptime"]
            oid_sysLocation = joid["basic_oids"]["oid_sysLocation"]
            oid_sysObjectID = joid["basic_oids"]["oid_sysObjectID"]

            # Получение данных по OID
            try:
                dirty_data = await SNMPFunctions.get_single_oid(host, oid_model, community)
                print(dirty_data)
                if not dirty_data:
                    raise ValueError(f"Не удалось получить данные по OID модели для хоста {host}")
                dirty_data = dirty_data.decode('utf-8') if isinstance(dirty_data, bytes) else str(dirty_data)
            except Exception as e:
                app_logger.error(f"Ошибка при получении данных OID модели для хоста {host}: {e}")
                return None

            sw_sys_name = await SNMPFunctions.get_single_oid(host, oid_sysname, community)
            if not sw_sys_name:
                raise ValueError(f"Не удалось получить имя устройства для хоста {host}")
            sw_sys_name = sw_sys_name.decode('utf-8') if isinstance(sw_sys_name, bytes) else str(sw_sys_name)

            sw_pen = await SNMPFunctions.get_single_oid(host, oid_sysObjectID, community)
            up_time = await SNMPFunctions.get_single_oid(host, oid_uptime, community)
            sys_location = await SNMPFunctions.get_single_oid(host, oid_sysLocation, community)

            if not sw_pen or not up_time or not sys_location:
                raise ValueError(f"Не удалось получить все необходимые данные для хоста {host}")

            parsed_oid = PENFinder.parse_oid(sw_pen)
            vendor = PENFinder.search_pen(parsed_oid['pen'])
            app_logger.debug(vendor[0].get('Organization'))

            # Парсинг sys_location
            result = HelperFunctions.parse_location(sys_location)
            address = (
                f"{result.get('country', 'Неизвестная страна')}, "
                f"{result.get('city', 'Неизвестный город')}, "
                f"{result.get('street', 'Неизвестная улица')}, "
                f"{result.get('house_number', '0')}"
            ) if result else "Неизвестный адрес"

            # Фильтрация модели устройства
            sw_model = DeviceUtils.filter_device_model(dirty_data)
            device_data = DeviceUtils.get_interface_config(dirty_data)

            # Фильтрация модели устройства и формирование uptime
            sw_up_time = HelperFunctions.seconds_to_str(up_time)

            return {
                "host": host,
                "vendor": vendor[0].get('Organization'),
                "sw_sys_name": sw_sys_name,
                "sw_model": sw_model,
                "sw_up_time": sw_up_time,
                "up_time": up_time,
                "device_data": device_data,
                "address": address,
                "latitude": result.get("latitude", 0.0) if result else 0.0,
                "longitude": result.get("longitude", 0.0) if result else 0.0,
            }

        except Exception as e:
            # Логирование ошибки с трассировкой
            app_logger.error(json.dumps({
                "date": current_date,
                "action": action,
                "host": host,
                "error": str(e),
                "trace": traceback.format_exc(),
            }))
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

    @staticmethod
    async def get_ddm_info(host: str, port_if_list: List[str], port_if_range: List[str], device_data, community: str) -> str:
        """
        Получает данные DDM или ADSL для указанного устройства.
        """
        action = "get_ddm_info"
        current_date = HelperFunctions.get_current_date()
        results = []
        joid = HelperFunctions.load_oids()

        try:
            # Получение модели устройства через SNMP
            model = DeviceUtils.filter_device_model(
                await SNMPFunctions.get_single_oid(host, joid["basic_oids"]["oid_model"], community))

            if port_if_list is None:
                list_of_ports = []

            if port_if_range is None:
                range_of_ports = []
            
            list_of_ports = port_if_list
            range_of_ports = port_if_range

            ddm_supported = device_data.get("ddm", False)
            adsl_supported = device_data.get("adsl", False)
            gpon_supported = device_data.get("gpon", False)

            # Логирование состояния устройства и поддержки
            app_logger.debug(f"Device data: {device_data}\n ddm_supported: {ddm_supported}, adsl_supported: {adsl_supported}, gpon_supported: {gpon_supported}")

            if ddm_supported:
                # Загрузка OID для определенной модели устройства
                oid_key_mapping = {
                    "snr_oids": "SNR",
                    "eltex_oids": "Eltex",
                    "dlink_oids": ["DGS", "DES"],
                    "cisco_oids": "SG200-26",
                    "ios_oids": "IOS",
                    "vsol_oid": "V1600G2B"
                }

                oid_loader_key = next(
                    (key for key, substr in oid_key_mapping.items() if HelperFunctions.model_contains_substr(model, substr)), "")

                if not oid_loader_key:
                    error_message = f"DDM не поддерживается для данной модели {model}."
                    app_logger.error({"date": current_date, "action": action, "error": error_message})
                    return error_message

                oid_loader = joid[oid_loader_key]

                # Обработка DDM данных для различных моделей
                if HelperFunctions.model_contains_substr(model, "SNR"):
                    await DeviceUtils.process_ddm_info(
                        host, list_of_ports, range_of_ports,
                        oid_loader["snr_oid_DDMRXPower"], oid_loader["snr_oid_DDMTXPower"],
                        oid_loader["snr_oid_DDMTemperature"], oid_loader["snr_oid_DDMVoltage"],
                        community, results
                    )
                elif HelperFunctions.model_contains_substr(model, ["Eltex MES14", "Eltex MES24", "Eltex MES3708"]):
                    await DeviceUtils.process_ddm_info(
                        host, list_of_ports, range_of_ports,
                        oid_loader["eltex_DDM_mes14_mes24_mes_3708"], oid_loader["eltex_DDM_mes14_mes24_mes_3708"],
                        oid_loader["eltex_DDM_mes14_mes24_mes_3708"], oid_loader["eltex_DDM_mes14_mes24_mes_3708"],
                        community, results, False, True, "access", HelperFunctions.convert_mW_to_dBW
                    )
                elif HelperFunctions.model_contains_substr(model, ["Eltex MES23", "Eltex MES33", "Eltex MES35", "Eltex MES53"]):
                    await DeviceUtils.process_ddm_info(
                        host, list_of_ports, range_of_ports,
                        oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"], oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"],
                        oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"], oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"],
                        community, results, True, True, 'aggregate'
                    )
                elif HelperFunctions.model_contains_substr(model, ["DGS-3620", "DES-3200", "DGS-3000"]):
                    await DeviceUtils.process_ddm_info(
                        host, list_of_ports, range_of_ports,
                        oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_rx_power"],
                        oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_tx_power"],
                        oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_temperature"],
                        oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_voltage"],
                        community, results
                    )
                elif HelperFunctions.model_contains_substr(model, "SG200-26"):
                    await DeviceUtils.process_ddm_info(
                        host, list_of_ports, range_of_ports,
                        oid_loader["cisco_DDM_S200"], oid_loader["cisco_DDM_S200"],
                        oid_loader["cisco_DDM_S200"], oid_loader["cisco_DDM_S200"],
                        community, results, True
                    )
                elif HelperFunctions.model_contains_substr(model, "V1600G2B"):
                    portDescr = await DeviceUtils.get_interface_range(host, community, oid_loader_key, "gponVsolupLinkPortDescr")
                    portIndex = await DeviceUtils.get_interface_list(host, community, oid_loader_key, "gponVsolupLinkPortIndex")
                    portType = HelperFunctions.to_string(await SNMPFunctions.get_multi_oid(
                        host, oid_loader["gponVsolupLinkPortType"], community
                    ), encoding='iso-8859-1')
                    
                    if not portIndex or not portDescr or not portType:
                        raise Exception(ErrorMessages.error_message(host))
                    # app_logger.info(f"{portDescr}\n {portIndex}")
                    port_types = {entry.oid.split('.')[-1]: entry.value for entry in portType}
                    type_of_ports = [value for key, value in port_types.items()]
                    
                    list_of_ports = [
                        portIndex[i] for i, port_type in enumerate(type_of_ports) if port_type == 0
                    ]  
                    range_of_ports = [
                        portDescr[i] for i, port_type in enumerate(type_of_ports) if port_type == 0
                    ]   

                    await DeviceUtils.process_ddm_info(
                        host, list_of_ports, range_of_ports,
                        oid_loader["transceiverReceivedPower"], oid_loader["transceiverTransmitPower"],
                        oid_loader["transceiverTemperature"], oid_loader["transceiverVoltage"],
                        community, results
                    )
                else:
                    error_message = f"DDM не поддерживается для устройства {host}."
                    HelperFunctions.log_error(action=action, host=host, error=ValueError(error_message))
                    return error_message
            elif adsl_supported:
                    # list_of_ports = [
                    await DeviceUtils.process_adsl_info(
                        host, list_of_ports, range_of_ports,
                        joid["adsl_oid"],
                        community, results, power_converter=HelperFunctions.adsl_val_converter
                    )
            else:
                    error_message = f"DDM не поддерживается для устройства {host}."
                    HelperFunctions.log_error(action=action, host=host, error=ValueError(error_message))
                    return error_message     
                   # port_if_range[i], snr_margin, attenuation, output_power, attainable_rate, tx_rate
            if not adsl_supported:
                return HelperFunctions.table_formatted_output(results, ["IF", "Tx", "Rx", "°C", "V"])
            elif adsl_supported:
                return HelperFunctions.table_formatted_output(results, ["IF", "snr_margin", "attenuation", "output_power", "attainable_rate", "tx_rate"])
        except PermissionError as e:
            error_message = f"Ошибка доступа к файлу: {e}. Возможно, у вас нет прав на чтение данного файла."
            HelperFunctions.log_error(action=action, host=host, error=e)
            return error_message
        except Exception as e:
            error_message = f"При проверке DDM на устройстве: {host} произошла ошибка: {e}"
            HelperFunctions.log_error(action=action, host=host, error=e)
            return error_message

    @staticmethod
    async def process_ddm_info(
            host: str,
            port_if_list: List[str],
            port_if_range: List[str],
            base_oid_rx_power: str,
            base_oid_tx_power: str,
            base_oid_temperature: str,
            base_oid_voltage: str,
            community: str,
            results: List[Any],
            unstandart: Optional[bool]=False,
            eltex: Optional[bool]=False,
            mib_type: str=None,
            power_converter: Optional[Callable[[float], float]]=None
    ) -> None:
        param_suffix_map = {
            "temperature": {True: ".5", False: ".1"},
            "voltage": {True: ".6", False: ".2"},
            "bias": {True: ".7", False: ".3"},
            "tx_power": {True: ".8", False: ".4"},
            "rx_power": {True: ".9", False: ".5"},
        }
        """Обрабатывает DDM информацию с устройства через SNMP."""
        for i, port in enumerate(port_if_list):

            def generate_oid(base_oid: str, suffix: str) -> str:
                if unstandart:
                    return f"{base_oid}{port}{suffix}"
                elif eltex:
                    if mib_type.lower() == "access":
                        full_oid = f"{base_oid}{port}{suffix}.1"
                    elif mib_type.lower() == "aggregate":
                        full_oid = f"{base_oid}{port}{suffix}"
                    else:
                        raise ValueError(f"Неизвестный тип MIB: {mib_type}")
                    return full_oid
                else:
                    return f"{base_oid}{port}"

            # Генерация OID для всех типов параметров
            oid_rx_power = generate_oid(base_oid_rx_power, param_suffix_map["rx_power"][unstandart])
            oid_tx_power = generate_oid(base_oid_tx_power, param_suffix_map["tx_power"][unstandart])
            oid_temperature = generate_oid(base_oid_temperature, param_suffix_map["temperature"][unstandart])
            oid_voltage = generate_oid(base_oid_voltage, param_suffix_map["voltage"][unstandart])

            get_rx_power = await SNMPFunctions.get_single_oid(host, oid_rx_power, community)
            get_tx_power = await SNMPFunctions.get_single_oid(host, oid_tx_power, community)
            get_temperature = await SNMPFunctions.get_single_oid(host, oid_temperature, community)
            get_voltage = await SNMPFunctions.get_single_oid(host, oid_voltage, community)

            if all(HelperFunctions.clean_and_convert(val) is not None for val in
                   [get_rx_power, get_tx_power, get_voltage, get_temperature]):

                ddm_rx_power = HelperFunctions.clean_and_convert(get_rx_power, scale=1000)
                ddm_tx_power = HelperFunctions.clean_and_convert(get_tx_power, scale=1000)
                ddm_voltage = HelperFunctions.clean_and_convert(get_voltage)
                ddm_temperature = HelperFunctions.clean_and_convert(get_temperature)
                app_logger.debug(port_if_range[i], ddm_tx_power, ddm_rx_power, ddm_voltage, ddm_temperature)
                # #
                if power_converter:
                    ddm_rx_power = power_converter(ddm_rx_power)
                    ddm_tx_power = power_converter(ddm_tx_power)
                    app_logger.debug(port_if_range[i], ddm_tx_power, ddm_rx_power, ddm_voltage, ddm_temperature)

                # if all(val not in ["-inf"] for val in
                #        [ddm_rx_power, ddm_tx_power, ddm_voltage, ddm_temperature]):
                results.append([port_if_range[i], ddm_tx_power, ddm_rx_power, ddm_temperature, ddm_voltage])

    @staticmethod
    async def get_lldp_data(host: str, community: str) -> Any:
        action = f"{__name__}.get_lldp_data"
        current_date = HelperFunctions.get_current_date()
        results = []

        joid = HelperFunctions.load_oids()
        oidRemSysName = joid["lldp_oids"]["lldpRemSysName"]
        oidRemSysModel = joid["lldp_oids"]["lldpRemSysDesc"]
        oidRemIfName = joid["lldp_oids"]["lldpRemPortId"]
        oidRemManIp = joid["lldp_oids"]["lldpRemManIp"]

        try:
            # Получаем данные для всех OID с параллельными запросами
            res_rem_sys_name, res_rem_sys_model, res_rem_sys_if_name, res_local_sys_name, res_local_model = await asyncio.gather(
                SNMPFunctions.get_multi_oid(host, oidRemSysName, community),
                SNMPFunctions.get_multi_oid(host, oidRemSysModel, community),
                SNMPFunctions.get_multi_oid(host, oidRemIfName, community),
                SNMPFunctions.get_single_oid(host, "1.3.6.1.2.1.1.5.0", community),
                SNMPFunctions.get_single_oid(host, "1.3.6.1.2.1.1.1.0", community)
            )
            # Преобразуем данные в строки, если это необходимо
            res_rem_sys_name = HelperFunctions.to_string(res_rem_sys_name)
            res_rem_sys_model = HelperFunctions.to_string(res_rem_sys_model)
            # Преобразование значений с учетом типа
            res_rem_sys_if_name = HelperFunctions.to_string(res_rem_sys_if_name)

            res_local_sys_name = HelperFunctions.to_string(res_local_sys_name)

        # Преобразование значений с учетом типа

            # Применение фильтрации модели устройства
            loaclSysModel = DeviceUtils.filter_device_model(res_local_model)

            # Преобразование значений с учетом типа
            sysName = [
                index[1].decode('utf-8') if isinstance(index[1], bytes) else str(index[1])
                for index in res_rem_sys_name
            ]
            sysModel = [
                DeviceUtils.filter_device_model(index[1].decode('utf-8') if isinstance(index[1], bytes) else str(index[1]))
                for index in res_rem_sys_model
            ]
            ifName = [
                index[1].decode('utf-8') if isinstance(index[1], bytes) else str(index[1])
                for index in res_rem_sys_if_name
            ]

            # loaclSysModel = [
            #     index[1].decode('utf-8') if isinstance(index[1], bytes) else str(index[1])
            #     for index in res_local_sys_model
            # ]

            # Обработка интерфейсов
            # Пример с использованием атрибутов объекта PyVarBind
            parsed_if_name = []
            for item in res_rem_sys_if_name:
                if isinstance(item, PyVarBind):  # Проверяем, что это объект PyVarBind
                    oid = item.oid
                    regex = r'(\d+)(?=,\d+$)'
                    oid_string = ','.join(str(x) for x in oid.split('.'))
                    match = re.search(regex, oid_string)
                    extracted_number = match.group(0) if match else None
                    if_name = HelperFunctions.to_string(await SNMPFunctions.get_single_oid(host, f"1.3.6.1.2.1.2.2.1.2.{extracted_number}", community))
                    parsed_if_name.append(if_name)

                # value = item.value
                    # Преобразуем значение в строку, если это необходимо
                    # str_value = value.decode('utf-8') if isinstance(value, bytes) else str(value)
                    # Логируем или используем str_value дальше
                else:
                    app_logger.error(f"Expected a PyVarBind, but got: {type(item)}")

            # Создание соединений
            # connections = [
            #     [
            #         # loaclSysModel,
            #         # res_local_sys_name,
            #         local_if_name,  # Пример значения интерфейса
            #         ifName[idx],
            #         sysName[idx],
            #         sysModel[idx],
            #     ]
            #     for idx, local_if_name in enumerate(parsed_if_name)
            # ]
            
            connections = np.array([
                (local_if_name, ifName[idx], sysName[idx], sysModel[idx])
                for idx, local_if_name in enumerate(parsed_if_name)
            ], dtype=[('local_if_name', 'U50'), ('if_name', 'U50'), ('sys_name', 'U50'), ('sys_model', 'U50')])

            # Возврат сгенерированного результата
            return connections  # Заменить на функцию генерации таблицы LLDP

        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return None

    @staticmethod
    async def process_adsl_info(
            host: str,
            port_if_list: List[str],
            port_if_range: List[str],
            adsl_oids: Dict[str, str],
            community: str,
            results: List[Any],
            mib_type: str=None,
            power_converter: Optional[Callable[[float], float]]=None
    ) -> None:

        """Обрабатывает ADSL информацию с устройства через SNMP."""
        for i, port in enumerate(port_if_list):

            def generate_oid(base_oid: str,) -> str:
                    return f"{base_oid}{port}"
            # oids_prefix = "atur" if not atuc else "atuc"

            # Генерация OID для всех типов параметров ADSL
            oid_atur_snr_margin = generate_oid(adsl_oids["adslAturCurrSnrMgn"],)
            oid_atur_attenuation = generate_oid(adsl_oids["adslAturCurrAtn"])
            oid_atur_output_power = generate_oid(adsl_oids["adslAturCurrOutputPwr"])
            oid_atur_attainable_rate = generate_oid(adsl_oids["adslAturCurrAttainableRate"])
            oid_atur_tx_rate = generate_oid(adsl_oids["adslAturChanCurrTxRate"])
            
            oid_atuc_snr_margin = generate_oid(adsl_oids["adslAtucCurrSnrMgn"],)
            oid_atuc_attenuation = generate_oid(adsl_oids["adslAtucCurrAtn"])
            oid_atuc_output_power = generate_oid(adsl_oids["adslAtucCurrOutputPwr"])
            oid_atuc_attainable_rate = generate_oid(adsl_oids["adslAtucCurrAttainableRate"])
            oid_atuc_tx_rate = generate_oid(adsl_oids["adslAtucChanCurrTxRate"])
            
            get_atur_snr_margin = await SNMPFunctions.get_single_oid(host, oid_atur_snr_margin, community)
            get_atur_attenuation = await SNMPFunctions.get_single_oid(host, oid_atur_attenuation, community)
            get_atur_output_power = await SNMPFunctions.get_single_oid(host, oid_atur_output_power, community)
            get_atur_attainable_rate = await SNMPFunctions.get_single_oid(host, oid_atur_attainable_rate, community)
            get_atur_tx_rate = await SNMPFunctions.get_single_oid(host, oid_atur_tx_rate, community)
            
            get_atuc_snr_margin = await SNMPFunctions.get_single_oid(host, oid_atuc_snr_margin, community)
            get_atuc_attenuation = await SNMPFunctions.get_single_oid(host, oid_atuc_attenuation, community)
            get_atuc_output_power = await SNMPFunctions.get_single_oid(host, oid_atuc_output_power, community)
            get_atuc_attainable_rate = await SNMPFunctions.get_single_oid(host, oid_atuc_attainable_rate, community)
            get_atuc_tx_rate = await SNMPFunctions.get_single_oid(host, oid_atuc_tx_rate, community)

            if all(HelperFunctions.clean_and_convert(val) is not None for val in
                [get_atur_snr_margin, get_atur_attenuation, get_atur_output_power, get_atur_attainable_rate, get_atur_tx_rate,
                 get_atuc_snr_margin, get_atuc_attenuation, get_atuc_output_power, get_atuc_attainable_rate, get_atuc_tx_rate]):

                atur_snr_margin = get_atur_snr_margin
                atuc_snr_margin = (get_atuc_snr_margin)
                atur_attenuation = (get_atur_attenuation)
                atuc_attenuation = (get_atuc_attenuation)
                atur_output_power = (get_atur_output_power)
                atuc_output_power = (get_atuc_attenuation)
                atur_attainable_rate = get_atur_attainable_rate
                atuc_attainable_rate = (get_atuc_attenuation)
                atur_tx_rate = get_atur_tx_rate
                atuc_tx_rate = (get_atuc_tx_rate)
                
                app_logger.debug(port_if_range[i], atur_snr_margin, atur_attenuation, atur_output_power, atur_attainable_rate, atur_tx_rate)

                # Применение конвертера мощности, если передан
                if power_converter:
                    atur_snr_margin = power_converter(atur_snr_margin)
                    atuc_snr_margin = power_converter(atuc_snr_margin)

                    atur_attenuation = power_converter(atur_attenuation)
                    atuc_attenuation = power_converter(atuc_attenuation)
                    
                    atur_output_power = power_converter(atur_output_power)
                    atuc_output_power = power_converter(atuc_output_power)

                    atur_attainable_rate = HelperFunctions.convert_to_mbps(atur_attainable_rate)
                    atuc_attainable_rate = HelperFunctions.convert_to_mbps(atuc_attainable_rate)
                    
                    atuc_tx_rate = HelperFunctions.convert_to_mbps(atuc_tx_rate)
                    atur_tx_rate = HelperFunctions.convert_to_mbps(atur_tx_rate)
                    
                results.append([port_if_range[i],
                                f"{atur_snr_margin}/{atuc_snr_margin}", 
                                f"{atur_attenuation}/{atuc_attenuation}", 
                                f"{atur_output_power}/{atuc_output_power}", 
                                f"{atur_attainable_rate}/{atuc_attainable_rate}", 
                                f"{atur_tx_rate}/{atuc_tx_rate}"
                                ])

