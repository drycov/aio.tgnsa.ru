import asyncio
from typing import Optional, List

from netaddr import IPNetwork
from ping3 import ping

from app.constants import NetworkMessages
from app.utils import HelperFunctions


class NetworkUtils:

    @staticmethod
    def subnet_calculate(network_address: str) -> str:
        """
        Подсчет информации о сети по IP-адресу и маске.
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
    def p2p_calculate(network_address: str) -> str:
        """
        Подсчет информации для P2P по IP-адресу и маске.
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
    def ping_device_log(host: str, count: int = 4) -> Optional[str]:
        """
        Пинг устройства с логированием.

        Args:
            host (str): IP-адрес или доменное имя устройства.
            count (int): Количество попыток пинга.

        Returns:
            Optional[str]: Лог результатов пинга с указанием времени отклика, либо None, если устройство недоступно.
        """
        action = f"{__name__}.ping_device_log"

        try:
            results: List[float] = []
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

            final_log = "\n".join(log_messages)
            return final_log

        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return None

    @staticmethod
    async def is_alive(host: str) -> bool:
        """
        Проверяет доступность устройства по IP-адресу.

        Args:
            host (str): IP-адрес или доменное имя устройства.

        Returns:
            bool: True, если устройство доступно, иначе False.
        """
        # Выполняем проверку пинга асинхронно
        action = f"{__name__}.is_alive"

        try:
            response = await asyncio.to_thread(ping, host, timeout=1)
            return response is not None
        except Exception as e:
            HelperFunctions.log_error(action=action, host=host, error=e)
            return False
