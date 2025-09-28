import asyncio
from contextlib import ExitStack
import ipaddress
import socket
import time
from typing import Dict, Optional, Tuple, Union, List
from ping3 import verbose_ping, ping
from traceroute import traceroute

from app.core.utils.decorators import handle_network_error

UDP_PORT = 33434


class NetworkUtils:
    """
    Универсальный набор асинхронных и синхронных утилит для диагностики IP-сетей.
    """
    from app.core.logging_setup import logger as _base_logger
    logger = _base_logger.bind(component="NetworkUtils")


    _dns_cache: dict[str, str] = {}

    @staticmethod
    @handle_network_error(default_return=(None, "⚠️ Внутренняя ошибка при проверке подсети"))
    async def validate_subnet(
        subnet: str,
    ) -> Tuple[Optional[ipaddress.IPv4Network], Optional[str]]:
        NetworkUtils.logger.info(f"Валидация подсети: {subnet}")
        try:
            net = ipaddress.IPv4Network(subnet, strict=False)
            NetworkUtils.logger.info(f"Подсеть успешно распознана: {net}")
        except ValueError as e:
            NetworkUtils.logger.info(f"Ошибка при парсинге подсети: {e}")
            return None, "❌ Некорректный формат подсети"

        if net.prefixlen < 8:
            NetworkUtils.logger.info(f"Подсеть слишком большая, prefixlen={net.prefixlen}")
            return None, "❌ Слишком большая подсеть (минимум /8)"
        if net.network_address.is_loopback:
            NetworkUtils.logger.info(f"Подсеть является loopback: {net.network_address}")
            return None, "❌ Loopback-адрес не используется для сканирования"
        if net.network_address.is_multicast:
            NetworkUtils.logger.info(f"Подсеть является multicast: {net.network_address}")
            return None, "❌ Multicast-адрес не подходит"

        NetworkUtils.logger.info(f"Подсеть валидна: {net}")
        return net, None

    @staticmethod
    async def validate_ip(ip: str) -> Tuple[Optional[ipaddress.IPv4Address], Optional[str]]:
        NetworkUtils.logger.info(f"Валидация IP: {ip}")
        try:
            addr = ipaddress.IPv4Address(ip)
            NetworkUtils.logger.info(f"IP валиден: {addr}")
            return addr, None
        except ipaddress.AddressValueError as e:
            NetworkUtils.logger.info(f"Ошибка валидации IP: {e}")
            return None, "❌ Неверный формат IP-адреса"

    @staticmethod
    @handle_network_error(default_return={"error": "⚠️ Ошибка анализа сети"})
    async def get_network_info(net: ipaddress.IPv4Network) -> Dict[str, Union[str, int, bool]]:
        NetworkUtils.logger.info(f"Получение информации о сети: {net}")
        hosts = list(net.hosts())
        first_host = str(hosts[0]) if hosts else "N/A"
        last_host = str(hosts[-1]) if hosts else "N/A"

        total_hosts = net.num_addresses - 2 if net.prefixlen < 31 else net.num_addresses

        info = {
            "network": str(net.network_address),
            "netmask": str(net.netmask),
            "broadcast": str(net.broadcast_address) if net.prefixlen < 31 else "N/A",
            "first_host": first_host,
            "last_host": last_host,
            "total_hosts": total_hosts,
            "hostmask": str(net.hostmask),
            "prefixlen": net.prefixlen,
            "is_private": net.is_private,
            "is_global": net.is_global,
            "is_point_to_point": net.prefixlen >= 31,
            "is_reserved": net.is_reserved,
            "is_loopback": net.network_address.is_loopback,
            "is_multicast": net.network_address.is_multicast,
            "is_unspecified": net.network_address.is_unspecified,
        }
        NetworkUtils.logger.info(f"Информация о сети: {info}")
        return info

    @staticmethod
    @handle_network_error(default_return=(False, None))
    async def is_alive(
        host: str,
        timeout: int = 2,
        count: int = 2,
        privileged: bool = True
    ) -> Tuple[bool, Optional[float]]:
        """
        Асинхронная проверка доступности IP-хоста через ICMP с несколькими попытками.
        """
        NetworkUtils.logger.info(f"Проверка доступности хоста {host} с таймаутом {timeout} и количеством попыток {count}")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            NetworkUtils.logger.info(f"Хост {host} не является IP, пропускаем пинг.")
            return False, None

        async def single_ping():
            return await asyncio.to_thread(ping, host, timeout=timeout, privileged=privileged)

        tasks = [single_ping() for _ in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_times = [r * 1000 for r in results if isinstance(r, (int, float)) and r is not None]

        if valid_times:
            avg_rtt = round(sum(valid_times) / len(valid_times), 2)
            NetworkUtils.logger.info(f"Хост {host} доступен, среднее время отклика {avg_rtt} мс")
            return True, avg_rtt
        else:
            NetworkUtils.logger.info(f"Хост {host} недоступен")
            return False, None

    @staticmethod
    @handle_network_error(default_return={
        "host": None,
        "reachable": False,
        "packets_sent": 0,
        "packets_received": 0,
        "packet_loss": 100.0,
        "min_rtt": None,
        "max_rtt": None,
        "avg_rtt": None,
        "errors": ["⚠️ Внутренняя ошибка"],
    })
    async def detailed_ping(host: str, timeout: int = 1, count: int = 4) -> Dict:
        """
        Параллельный расширенный пинг с подсчетом RTT и потерь.
        """
        NetworkUtils.logger.info(f"Расширенный пинг хоста {host} с таймаутом {timeout} и {count} попытками")

        async def ping_once(seq: int):
            delay = await asyncio.to_thread(ping, host, timeout=timeout, seq=seq)
            return delay

        tasks = [ping_once(i + 1) for i in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        rtt_times = [round(r * 1000, 2) for r in results if isinstance(r, (float, int)) and r is not None]

        packets_received = len(rtt_times)
        packet_loss = round((count - packets_received) / count * 100, 1) if count else 100.0

        NetworkUtils.logger.info(f"Пинг {host}: получено {packets_received}/{count} ответов, потеря пакетов {packet_loss}%")

        return {
            "host": host,
            "reachable": packets_received > 0,
            "packets_sent": count,
            "packets_received": packets_received,
            "packet_loss": packet_loss,
            "min_rtt": min(rtt_times) if rtt_times else None,
            "max_rtt": max(rtt_times) if rtt_times else None,
            "avg_rtt": round(sum(rtt_times) / packets_received, 2) if packets_received else None,
            "errors": [],
        }

    @staticmethod
    @handle_network_error(default_return=None)
    def ping_device_log(host: str, count: int = 4) -> Optional[str]:
        """
        Синхронный пинг с формированием лог-отчёта.
        """
        NetworkUtils.logger.info(f"Синхронный пинг устройства {host} с {count} попытками")
        results = []
        log_messages = []

        for i in range(count):
            response_time = ping(host)
            if response_time is not None:
                rtt = response_time * 1000
                results.append(rtt)
                log_messages.append(f"Время отклика от {host} (попытка {i + 1}): {rtt:.2f} мс")
            else:
                log_messages.append(f"Попытка {i + 1}: Устройство {host} недоступно.")

        if results:
            avg_ping = sum(results) / len(results)
            log_messages.append(f"Среднее время отклика от {host}: {avg_ping:.2f} мс")
            NetworkUtils.logger.info(f"Среднее время отклика от {host}: {avg_ping:.2f} мс")
        else:
            log_messages.append(f"Устройство {host} недоступно.")
            NetworkUtils.logger.info(f"Устройство {host} недоступно после {count} попыток.")

        return "\n".join(log_messages)

    @classmethod
    async def resolve_ip(cls, host: str) -> Optional[str]:
        NetworkUtils.logger.info(f"Разрешение IP для хоста: {host}")
        if host in cls._dns_cache:
            NetworkUtils.logger.info(f"IP найден в кэше: {cls._dns_cache[host]}")
            return cls._dns_cache[host]
        try:
            addr = ipaddress.ip_address(host)
            cls._dns_cache[host] = str(addr)
            NetworkUtils.logger.info(f"Хост уже IP: {addr}")
            return str(addr)
        except ValueError:
            try:
                import socket
                ip = socket.gethostbyname(host)
                cls._dns_cache[host] = ip
                NetworkUtils.logger.info(f"Хост {host} разрешён в IP {ip}")
                return ip
            except socket.gaierror as e:
                NetworkUtils.logger.info(f"Не удалось разрешить хост {host}: {e}")
                return None