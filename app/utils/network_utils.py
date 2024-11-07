import os
import platform
import json
from enum import Enum
from netaddr import IPNetwork
from ping3 import ping
from typing import Any, Optional

from app.constants import NetworkMessages


class NetworkUtils:

    @staticmethod
    def subnet_calculate(network_address: str) -> str:
        """
        Подсчет информации о сети по IP-адресу и маске.
        """
        try:
            subnet = IPNetwork(network_address)
            return NetworkMessages.NETWORK_INFO.value.format(
                network=subnet.network,
                netmask=subnet.netmask,
                first=subnet[1],
                last=subnet[-2],
                size=subnet.size - 2
            )
        except Exception as error:
            print(NetworkMessages.ERROR_SUBNET_CALCULATION.value.format(error=error))
            return NetworkMessages.ERROR_SUBNET_FORMAT.value

    @staticmethod
    def p2p_calculate(network_address: str) -> str:
        """
        Подсчет информации для P2P по IP-адресу и маске.
        """
        try:
            p2p_subnet = IPNetwork(network_address)
            return NetworkMessages.P2P_INFO.value.format(
                host=p2p_subnet[-2],
                gateway=p2p_subnet[1],
                netmask=p2p_subnet.netmask
            )
        except Exception as error:
            print(NetworkMessages.ERROR_P2P_CALCULATION.value.format(error=error))
            return NetworkMessages.ERROR_P2P_FORMAT.value

    @staticmethod
    def ping_device_log(host: str, count: int = 4) -> Optional[float]:
        """
        Пинг устройства с логированием.
        """
        extra_options = ["-c", str(count)] if platform.system() == "Linux" else ["-n", str(count)]

        try:
            result = ping(host, count=count)  # ping3 returns None if unreachable
            return result
        except Exception as error:
            print(NetworkMessages.ERROR_PING.value.format(error=error))
            return None

