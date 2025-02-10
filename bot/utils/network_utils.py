import asyncio
import ipaddress
from typing import Dict, List, Optional, Tuple

from netaddr import IPNetwork
from ping3 import ping

from bot.constants import NetworkMessages
from .device_utils import DeviceUtils
from .helper_functions import HelperFunctions
from .snmp_functions import SNMPFunctions
from bot.utils.logger_instance import app_logger


class NetworkUtils:

    @staticmethod
    def subnet_calculate(network_address: str) -> str:
        """
        Подсчет информации о сети по IP-адресу и маске.
        :param network_address: IP-адрес и маска сети (например, "192.168.1.0/24").
        :return: Строка с информацией о сети или сообщение об ошибке.
        """
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
        """
        Проверяет доступность устройства по IP-адресу.
        :param host: IP-адрес или доменное имя устройства.
        :return: True, если устройство доступно, иначе False.
        """
        action = f"{__name__}.is_alive"
        try:
            response = await asyncio.to_thread(ping, host, timeout=1)
            return response is not None
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return False

    async def subnet_scan_with_info(self, subnet: str, communities: List[str]) -> List[Dict[str, str]]:
        """
        Сканирует подсеть на доступность устройств и собирает базовую информацию через SNMP.
        :param subnet: Подсеть для сканирования (например, "192.168.1.0/24").
        :param communities: Список SNMP community strings для проверки.
        :return: Список словарей с информацией о доступных устройствах.
        """
        action = f"{__name__}.subnet_scan_with_info"
        from ..bot_instance import ertm
        # print(communities)
        try:
            network = ipaddress.ip_network(subnet, strict=False)
            ip_list = [str(ip) for ip in network.hosts()]

            app_logger.info(f"Начинаем сканирование подсети {subnet}...")
            alive_hosts = await self._get_alive_hosts(ip_list)
            # print(alive_hosts)
            if not alive_hosts:
                app_logger.info(f"Нет доступных устройств в подсети {subnet}.")
                return []

            app_logger.info(f"Найдено доступных устройств: {len(alive_hosts)}. Проверяем SNMP...")
            valid_hosts = await self._check_snmp_communities(hosts=alive_hosts, communities=communities)
            # print(valid_hosts)
            if not valid_hosts:
                print("Нет устройств с доступным SNMP.")
                return []

            app_logger.info(f"Собираем информацию с {len(valid_hosts)} устройств через SNMP...")
            device_info = await self._collect_device_info(valid_hosts, ertm)
            # print(device_info)
            # Фильтруем устройства без данных SNMP
            filtered_info = [info for info in device_info if info]
            # print(filtered_info)
            app_logger.info(f"Оставлено {len(filtered_info)} устройств с данными SNMP.")
            return filtered_info

        except ValueError as e:
            app_logger.error(f"Ошибка: некорректная подсеть {subnet}: {e}")
            HelperFunctions.log_error(action=action, host=subnet, error=e)
            return []
        except Exception as e:
            app_logger.error(f"Неизвестная ошибка при сканировании подсети: {e}")
            HelperFunctions.log_error(action=action, host=subnet, error=e)
            return []

    async def _get_alive_hosts(self, ip_list: List[str]) -> List[str]:
        """Возвращает список доступных хостов."""
        tasks = [self.is_alive(ip) for ip in ip_list]
        results = await asyncio.gather(*tasks)
        return [ip for ip, is_alive in zip(ip_list, results) if is_alive]

    @staticmethod
    async def _check_snmp_communities(hosts: List[str], communities: List[str]) -> List[Tuple[str, str]]:
        """Проверяет SNMP community strings для списка хостов."""
        tasks = [SNMPFunctions.check_snmp(host=host, communities=communities) for host in hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [(host, community) for host, community in zip(hosts, results) if isinstance(community, str)]

    @staticmethod
    async def _collect_device_info(hosts: List[Tuple[str, str]], ertm) -> List[Dict[str, str]]:
        """Собирает информацию об устройствах через SNMP."""
        tasks = [DeviceUtils.get_basic_info(host, community) for host, community in hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_devices = []
        for (host, community), result in zip(hosts, results):
            if isinstance(result, dict):
                ertm.add_device(
                    host=host,
                    sys_name=result.get('sw_sys_name', 'nAn'),
                    model=result.get('sw_model', 'nAn'),
                    latitude=result.get('latitude', 0),
                    longitude=result.get('longitude', 0),
                    address=result.get('address', 'nAn'),
                    vendor=result.get('vendor', 'nAn'),
                )
                valid_devices.append(result)
            else:
                print(f"Ошибка при обработке {host}: {result}")

        return valid_devices

    @staticmethod
    def p2p_calculate(network_address: str) -> str:
        """
        Подсчет информации для P2P по IP-адресу и маске.
        :param network_address: IP-адрес и маска сети (например, "192.168.1.0/30").
        :return: Строка с информацией о P2P или сообщение об ошибке.
        """
        action = f"{__name__}.p2p_calculate"
        try:
            p2p_subnet = IPNetwork(network_address)
            return NetworkMessages.P2P_INFO.value.format(
                pair_address=p2p_subnet[0],
                host=p2p_subnet[-2],
                gateway=p2p_subnet[1],
                netmask=p2p_subnet.netmask
            )
        except Exception as e:
            HelperFunctions.log_error(action=action, host=network_address, error=e)
            return NetworkMessages.ERROR_P2P_FORMAT.value

    @staticmethod
    def ping_device_log(host: str, count: int=4) -> Optional[str]:
        """
        Пинг устройства с логированием.
        :param host: IP-адрес или доменное имя устройства.
        :param count: Количество попыток пинга.
        :return: Лог результатов пинга с указанием времени отклика, либо None, если устройство недоступно.
        """
        action = f"{__name__}.ping_device_log"
        try:
            results = []
            log_messages = []
            for i in range(count):
                response_time = ping(host)
                if response_time is not None:
                    response_time_ms = response_time * 1000
                    results.append(response_time_ms)
                    log_messages.append(f"Время отклика от {host} (попытка {i + 1}): {response_time_ms:.2f} мс")
                else:
                    log_messages.append(f"Попытка {i + 1}: Устройство {host} недоступно.")

            if results:
                average_ping = sum(results) / len(results)
                log_messages.append(f"Среднее время отклика от {host}: {average_ping:.2f} мс")
            else:
                log_messages.append(f"Устройство {host} недоступно.")

            return "\n".join(log_messages)

        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return None
