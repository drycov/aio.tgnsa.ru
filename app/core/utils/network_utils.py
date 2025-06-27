import asyncio
import ipaddress
import logging
from typing import Dict, Optional, Tuple, Union, List
from ping3 import ping

from app.core.utils.decorators import handle_network_error

logger = logging.getLogger(__name__)


class NetworkUtils:
    """
    Универсальный набор асинхронных и синхронных утилит для диагностики IP-сетей:
    - Валидация подсетей
    - Получение параметров сетей
    - Проверка доступности хостов
    - Расширенный ICMP-пинг
    - Логирование результатов пинга
    """

    @staticmethod
    @handle_network_error(
        default_return=(None, "⚠️ Внутренняя ошибка при проверке подсети")
    )
    async def validate_subnet(
        subnet: str,
    ) -> Tuple[Optional[ipaddress.IPv4Network], Optional[str]]:
        """
        Валидирует IPv4-подсеть и возвращает объект сети при допустимом префиксе и адресе.

        :param subnet: Строка подсети (например, '192.168.1.0/24')
        :return: Кортеж (объект сети, сообщение об ошибке при наличии)
        """
        net = ipaddress.IPv4Network(subnet, strict=False)

        if net.prefixlen < 8:
            return None, "❌ Слишком большая подсеть (минимум /8)"
        if net.network_address.is_loopback:
            return None, "❌ Loopback-адрес не используется для сканирования"
        if net.network_address.is_multicast:
            return None, "❌ Multicast-адрес не подходит"

        return net, None

    @staticmethod
    @handle_network_error(default_return={"error": "⚠️ Ошибка анализа сети"})
    async def get_network_info(
        net: ipaddress.IPv4Network,
    ) -> Dict[str, Union[str, int, bool]]:
        """
        Извлекает ключевые параметры из заданной IPv4-сети:
        - сетевой адрес
        - маска
        - количество хостов
        - приватность и тип адреса

        :param net: Объект ipaddress.IPv4Network
        :return: Словарь с параметрами сети
        """
        hosts = list(net.hosts())
        first_host, last_host = (hosts[0], hosts[-1]) if hosts else (None, None)

        total_hosts = (
            net.num_addresses if net.prefixlen >= 31 else net.num_addresses - 2
        )

        return {
            "network": str(net.network_address),
            "netmask": str(net.netmask),
            "broadcast": str(net.broadcast_address) if net.prefixlen < 31 else "N/A",
            "first_host": str(first_host) if first_host else "N/A",
            "last_host": str(last_host) if last_host else "N/A",
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

    @staticmethod
    @handle_network_error(default_return=(False, None))
    async def is_alive(
        host: str, timeout: int = 2, count: int = 2, privileged: bool = True
    ) -> Tuple[bool, Optional[float]]:
        """
        Асинхронная проверка доступности IP-хоста через ICMP.

        :param host: IP-адрес или имя хоста
        :param timeout: Таймаут на одну попытку (секунды)
        :param count: Количество попыток пинга
        :param privileged: Использовать "сырые" привилегии
        :return: Кортеж (True/False, среднее RTT в мс или None)
        """
        try:
            ipaddress.ip_address(host)
        except ValueError:
            try:
                ipaddress.ip_network(host)
                return False, None
            except ValueError:
                pass

        total_time = 0.0
        success_count = 0

        for _ in range(count):
            delay = await asyncio.to_thread(
                ping, host, timeout=timeout, privileged=privileged
            )
            if delay is not None and isinstance(delay, (int, float)):
                total_time += delay * 1000
                success_count += 1

        if success_count:
            return True, round(total_time / success_count, 2)
        return False, None

    @staticmethod
    @handle_network_error(
        default_return={
            "host": None,
            "reachable": False,
            "packets_sent": 0,
            "packets_received": 0,
            "packet_loss": 100.0,
            "min_rtt": None,
            "max_rtt": None,
            "avg_rtt": None,
            "errors": ["⚠️ Внутренняя ошибка"],
        }
    )
    async def detailed_ping(
        host: str, timeout: int = 1, count: int = 4
    ) -> Dict[str, Union[str, bool, int, float, None, list]]:
        """
        Расширенный пинг с измерением:
        - Минимального/максимального/среднего RTT
        - Процент потерь пакетов

        :param host: IP-адрес/домен
        :param timeout: Таймаут одной попытки
        :param count: Количество попыток
        :return: Подробный отчет по результатам пинга
        """
        results = {
            "host": host,
            "reachable": False,
            "packets_sent": count,
            "packets_received": 0,
            "packet_loss": 100.0,
            "min_rtt": None,
            "max_rtt": None,
            "avg_rtt": None,
            "errors": [],
        }

        rtt_times: List[float] = []

        for i in range(count):
            delay = await asyncio.to_thread(ping, host, timeout=timeout, seq=i + 1)
            if delay is not None:
                rtt = round(delay * 1000, 2)
                rtt_times.append(rtt)
                results["packets_received"] += 1

                results["min_rtt"] = min(results["min_rtt"] or rtt, rtt)
                results["max_rtt"] = max(results["max_rtt"] or rtt, rtt)

        if rtt_times:
            results["reachable"] = True
            results["packet_loss"] = round((count - len(rtt_times)) / count * 100, 1)
            results["avg_rtt"] = round(sum(rtt_times) / len(rtt_times), 2)

        return results

    @staticmethod
    @handle_network_error(default_return=None)
    def ping_device_log(host: str, count: int = 4) -> Optional[str]:
        """
        Выполняет ping и формирует строку лога по результатам ICMP-ответов.

        :param host: IP-адрес или DNS-имя
        :param count: Кол-во попыток
        :return: Готовый многострочный лог-отчет или None при ошибке
        """
        results = []
        log_messages = []

        for i in range(count):
            response_time = ping(host)
            if response_time is not None:
                rtt = response_time * 1000
                results.append(rtt)
                log_messages.append(
                    f"Время отклика от {host} (попытка {i + 1}): {rtt:.2f} мс"
                )
            else:
                log_messages.append(f"Попытка {i + 1}: Устройство {host} недоступно.")

        if results:
            avg_ping = sum(results) / len(results)
            log_messages.append(f"Среднее время отклика от {host}: {avg_ping:.2f} мс")
        else:
            log_messages.append(f"Устройство {host} недоступно.")

        return "\n".join(log_messages)
