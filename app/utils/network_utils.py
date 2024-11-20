import asyncio
import ipaddress
from typing import List

from netaddr import IPNetwork
from ping3 import ping

from app.constants import NetworkMessages
from .device_utils import DeviceUtils
from .helper_functions import HelperFunctions
from .snmp_functions import SNMPFunctions


class NetworkUtils:

    @staticmethod
    def subnet_calculate(network_address: str) -> str:
        action = f"{__name__}.subnet_calculate"
        try:
            subnet = IPNetwork(network_address)
            return NetworkMessages.NETWORK_INFO.value.format(
                network=subnet.network,
                netmask=subnet.netmask,
                first=subnet[1],
                last=subnet[-2],
                size=subnet.size - 2
            )
        except Exception as e:
            HelperFunctions.log_error(action=action, host=network_address, error=e)
            return NetworkMessages.ERROR_SUBNET_FORMAT.value

    @staticmethod
    async def is_alive(host: str) -> bool:
        action = f"{__name__}.is_alive"
        try:
            response = await asyncio.to_thread(ping, host, timeout=1)
            return response is not None
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return False

    @staticmethod
    async def subnet_scan_with_info(subnet: str, communities: List[str]) -> List[dict]:
        """
        Сканирует подсеть на доступность устройств и собирает базовую информацию через SNMP.
        """
        action = f"{__name__}.subnet_scan_with_info"
        from ..bot_instance import ertm

        try:
            # Получаем список всех IP-адресов в подсети
            network = ipaddress.ip_network(subnet, strict=False)
            ip_list = list(network.hosts())

            # Проверяем доступность хостов
            print(f"Начинаем сканирование подсети {subnet}...")
            tasks = [NetworkUtils.is_alive(str(ip)) for ip in ip_list]
            results = await asyncio.gather(*tasks)

            available_hosts = [str(ip) for ip, is_alive in zip(ip_list, results) if is_alive]
            if not available_hosts:
                print(f"Нет доступных устройств в подсети {subnet}.")
                return []

            print(f"Найдено доступных устройств: {len(available_hosts)}. Проверяем SNMP...")

            # Проверяем SNMP community string для каждого хоста
            community_tasks = [
                SNMPFunctions.check_snmp(host, communities) for host in available_hosts
            ]
            community_results = await asyncio.gather(*community_tasks, return_exceptions=True)

            valid_hosts = [
                (host, community)
                for host, community in zip(available_hosts, community_results)
                if isinstance(community, str)  # Проверяем, что результат успешный
            ]

            if not valid_hosts:
                print("Нет устройств с доступным SNMP.")
                return []

            print(f"Собираем информацию с {len(valid_hosts)} устройств через SNMP...")

            # Собираем информацию через SNMP
            info_tasks = [
                DeviceUtils.get_basic_info(host, community)
                for host, community in valid_hosts
            ]
            device_info_results = await asyncio.gather(*info_tasks, return_exceptions=True)

            valid_devices = []
            for host, result in zip(valid_hosts, device_info_results):
                if not isinstance(result, Exception) and result is not None:
                    host, community = host
                    if isinstance(result, dict):
                        ertm.add_device(
                            host=host,
                            sys_name=result.get('sw_sys_name', 'nAn'),
                            model=result.get('sw_model', 'nAn'),
                            latitude=result.get('latitude', 0),
                            longitude=result.get('longitude', 0),
                            address=result.get('address', 'nAn'),
                        )
                        valid_devices.append(result)
                    else:
                        print(f"Ошибка при обработке {host}: {result}")

            print(f"Найдено устройств с данными: {len(valid_devices)}.")
            return valid_devices

        except ValueError as e:
            print(f"Ошибка: некорректная подсеть {subnet}: {e}")
            HelperFunctions.log_error(action=action, host=subnet, error=e)
            return []
        except Exception as e:
            print(f"Неизвестная ошибка при сканировании подсети: {e}")
            HelperFunctions.log_error(action=action, host=subnet, error=e)
            return []
