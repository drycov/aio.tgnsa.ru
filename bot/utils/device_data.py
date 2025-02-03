import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Callable
from puresnmp.varbind import PyVarBind
from bot.constants import LogMessages, Symbols, ErrorMessages
from bot.utils.device_utils import DeviceUtils
from config import Config
from .helper_functions import HelperFunctions
from .logger_instance import app_logger
from .pen_finder import PENFinder
from .snmp_functions import SNMPFunctions
import numpy as np

current_date = HelperFunctions.get_current_date()



class DeviceData:
    
    device_data = HelperFunctions.load_device_data()

    @staticmethod
    async def process_adsl_info(host, list_of_ports, range_of_ports, community,model,results):
            action = "get_adsl_info"
            joid = HelperFunctions.load_oids()


        # Загрузка OID для определенной модели устройства


            # oid_loader_key = next(
            #     (key for key, substr in oid_key_mapping.items() if
            #      HelperFunctions.model_contains_substr(model, substr)), "")

            # if not oid_loader_key:
            #     error_message = f"ADSL не поддерживается для данной модели {model}."
            #     app_logger.error({"date": current_date, "action": action, "error": error_message})
            #     return error_message
            #
            oid_loader = joid["adsl_oid"]
            #
            # # Обработка DDM данных для различных моделей
            # if HelperFunctions.model_contains_substr(model, "SNR"):
            #     await DeviceUtils.process_ddm_info(
            #         host, list_of_ports, range_of_ports,
            #         oid_loader["snr_oid_DDMRXPower"], oid_loader["snr_oid_DDMTXPower"],
            #         oid_loader["snr_oid_DDMTemperature"], oid_loader["snr_oid_DDMVoltage"],
            #         community, results
            #     )
            # #
            # elif HelperFunctions.model_contains_substr(model, ["Eltex MES14", "Eltex MES24", "Eltex MES3708"]):
            #     await DeviceUtils.process_ddm_info(
            #         host, list_of_ports, range_of_ports,
            #         oid_loader["eltex_DDM_mes14_mes24_mes_3708"], oid_loader["eltex_DDM_mes14_mes24_mes_3708"],
            #         oid_loader["eltex_DDM_mes14_mes24_mes_3708"], oid_loader["eltex_DDM_mes14_mes24_mes_3708"],
            #         community, results, False, True, "access", HelperFunctions.convert_mW_to_dBW
            #     )
            # #
            # elif HelperFunctions.model_contains_substr(model,
            #                                            ["Eltex MES23", "Eltex MES33", "Eltex MES35", "Eltex MES53"]):
            #     await DeviceUtils.process_ddm_info(
            #         host, list_of_ports, range_of_ports,
            #         oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"], oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"],
            #         oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"], oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"],
            #         community, results, True, True, 'aggregate'
            #     )
            # #
            # elif HelperFunctions.model_contains_substr(model, ["DGS-3620", "DES-3200", "DGS-3000"]):
            #     await DeviceUtils.process_ddm_info(
            #         host, list_of_ports, range_of_ports,
            #         oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_rx_power"],
            #         oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_tx_power"],
            #         oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_temperature"],
            #         oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_voltage"],
            #         community, results
            #     )
            # #
#               "adsl_oid": {
#     "adslAtucCurrSnrMgn": ".1.3.6.1.2.1.10.94.1.1.2.1.4.",
#     "adslAtucCurrAtn": ".1.3.6.1.2.1.10.94.1.1.2.1.5.",
#     "adslAtucCurrOutputPwr": ".1.3.6.1.2.1.10.94.1.1.2.1.7.",
#     "adslAtucCurrAttainableRate": ".1.3.6.1.2.1.10.94.1.1.2.1.8.",
#     "adslAtucChanCurrTxRate": ".1.3.6.1.2.1.10.94.1.1.4.1.2.",
#     "adslAtucChanPrevTxRate": ".1.3.6.1.2.1.10.94.1.1.4.1.3.",
#     "adslAturCurrSnrMgn": ".1.3.6.1.2.1.10.94.1.1.3.1.4.",
#     "adslAturCurrAtn": ".1.3.6.1.2.1.10.94.1.1.3.1.5.",
#     "adslAturCurrOutputPwr": ".1.3.6.1.2.1.10.94.1.1.3.1.7.",
#     "adslAturCurrAttainableRate": ".1.3.6.1.2.1.10.94.1.1.3.1.8.",
#     "adslAturChanCurrTxRate": ".1.3.6.1.2.1.10.94.1.1.5.1.2.",
#     "adslAturChanPrevTxRate": ".1.3.6.1.2.1.10.94.1.1.5.1.3."
#   },
            DeviceUtils.process_ddm_info(
                    host, list_of_ports, range_of_ports,
                    oid_loader["cisco_DDM_S200"], oid_loader["cisco_DDM_S200"],
                    oid_loader["cisco_DDM_S200"], oid_loader["cisco_DDM_S200"],
                    community, results, True
                )

    async def process_gpon_info(host, list_of_ports, range_of_ports, community,model,results):
            action = f"{__name__}.process_gpon_info"
            joid = HelperFunctions.load_oids()


        # Загрузка OID для определенной модели устройства
            oid_key_mapping = {
                "snr_oids": "SNR",
                "eltex_oids": "Eltex",
                "dlink_oids": ["DGS", "DES"],
                "cisco_oids": "SG200-26",
                "ios_oids": "IOS"
            }

            oid_loader_key = next(
                (key for key, substr in oid_key_mapping.items() if
                 HelperFunctions.model_contains_substr(model, substr)), "")

            if not oid_loader_key:
                error_message = f"DDM не поддерживается для данной модели {model}."
                app_logger.error({"date": current_date, "action": action, "error": error_message})
                return error_message
            #
            oid_loader = joid[oid_loader_key]
            #
            # # Обработка DDM данных для различных моделей
            if HelperFunctions.model_contains_substr(model, "SNR"):
                await DeviceUtils.process_ddm_info(
                    host, list_of_ports, range_of_ports,
                    oid_loader["snr_oid_DDMRXPower"], oid_loader["snr_oid_DDMTXPower"],
                    oid_loader["snr_oid_DDMTemperature"], oid_loader["snr_oid_DDMVoltage"],
                    community, results
                )
            #
            elif HelperFunctions.model_contains_substr(model, ["Eltex MES14", "Eltex MES24", "Eltex MES3708"]):
                await DeviceUtils.process_ddm_info(
                    host, list_of_ports, range_of_ports,
                    oid_loader["eltex_DDM_mes14_mes24_mes_3708"], oid_loader["eltex_DDM_mes14_mes24_mes_3708"],
                    oid_loader["eltex_DDM_mes14_mes24_mes_3708"], oid_loader["eltex_DDM_mes14_mes24_mes_3708"],
                    community, results, False, True, "access", HelperFunctions.convert_mW_to_dBW
                )
            #
            elif HelperFunctions.model_contains_substr(model,
                                                       ["Eltex MES23", "Eltex MES33", "Eltex MES35", "Eltex MES53"]):
                await DeviceUtils.process_ddm_info(
                    host, list_of_ports, range_of_ports,
                    oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"], oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"],
                    oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"], oid_loader["eltex_DDM_mes23_mes33_mes35_mes53"],
                    community, results, True, True, 'aggregate'
                )
            #
            elif HelperFunctions.model_contains_substr(model, ["DGS-3620", "DES-3200", "DGS-3000"]):
                await DeviceUtils.process_ddm_info(
                    host, list_of_ports, range_of_ports,
                    oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_rx_power"],
                    oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_tx_power"],
                    oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_temperature"],
                    oid_loader["dlink_dgs36xx_ses32xx_dgs_30xx_ddm_voltage"],
                    community, results
                )
            #
            elif HelperFunctions.model_contains_substr(model, "SG200-26"):
                await DeviceUtils.process_ddm_info(
                    host, list_of_ports, range_of_ports,
                    oid_loader["cisco_DDM_S200"], oid_loader["cisco_DDM_S200"],
                    oid_loader["cisco_DDM_S200"], oid_loader["cisco_DDM_S200"],
                    community, results, True
                )
