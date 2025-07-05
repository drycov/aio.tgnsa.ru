import asyncio
import ipaddress
from typing import Dict, Optional, Tuple, Union, List
from ping3 import verbose_ping,ping
from traceroute import traceroute

from app.core.utils.decorators import handle_network_error
from app.core.logging_setup import logger


class NetworkUtils:
    """
    Универсальный набор асинхронных и синхронных утилит для диагностики IP-сетей.
    """
    _dns_cache: dict[str, str] = {}

    @staticmethod
    @handle_network_error(default_return=(None, "⚠️ Внутренняя ошибка при проверке подсети"))
    async def validate_subnet(
        subnet: str,
    ) -> Tuple[Optional[ipaddress.IPv4Network], Optional[str]]:
        try:
            net = ipaddress.IPv4Network(subnet, strict=False)
        except ValueError:
            return None, "❌ Некорректный формат подсети"

        if net.prefixlen < 8:
            return None, "❌ Слишком большая подсеть (минимум /8)"
        if net.network_address.is_loopback:
            return None, "❌ Loopback-адрес не используется для сканирования"
        if net.network_address.is_multicast:
            return None, "❌ Multicast-адрес не подходит"

        return net, None

    @staticmethod
    async def validate_ip(ip: str) -> Tuple[Optional[ipaddress.IPv4Address], Optional[str]]:
        try:
            addr = ipaddress.IPv4Address(ip)
            return addr, None
        except ipaddress.AddressValueError:
            return None, "❌ Неверный формат IP-адреса"

    @staticmethod
    @handle_network_error(default_return={"error": "⚠️ Ошибка анализа сети"})
    async def get_network_info(net: ipaddress.IPv4Network) -> Dict[str, Union[str, int, bool]]:
        hosts = list(net.hosts())
        first_host = str(hosts[0]) if hosts else "N/A"
        last_host = str(hosts[-1]) if hosts else "N/A"

        total_hosts = net.num_addresses - 2 if net.prefixlen < 31 else net.num_addresses

        return {
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
        try:
            ipaddress.ip_address(host)
        except ValueError:
            # Если не IP — не пингуем, сразу False
            return False, None

        async def single_ping():
            return await asyncio.to_thread(ping, host, timeout=timeout, privileged=privileged)

        tasks = [single_ping() for _ in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_times = [r * 1000 for r in results if isinstance(r, (int, float)) and r is not None]

        if valid_times:
            avg_rtt = round(sum(valid_times) / len(valid_times), 2)
            return True, avg_rtt
        else:
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
        async def ping_once(seq: int):
            delay = await asyncio.to_thread(ping, host, timeout=timeout, seq=seq)
            return delay

        tasks = [ping_once(i + 1) for i in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        rtt_times = [round(r * 1000, 2) for r in results if isinstance(r, (float, int)) and r is not None]

        packets_received = len(rtt_times)
        packet_loss = round((count - packets_received) / count * 100, 1) if count else 100.0

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
        else:
            log_messages.append(f"Устройство {host} недоступно.")

        return "\n".join(log_messages)

    @classmethod
    async def resolve_ip(cls, host: str) -> Optional[str]:
        if host in cls._dns_cache:
            return cls._dns_cache[host]
        try:
            addr = ipaddress.ip_address(host)
            cls._dns_cache[host] = str(addr)
            return str(addr)
        except ValueError:
            try:
                # Можно использовать async DNS resolver, например aiodns
                import socket
                ip = socket.gethostbyname(host)
                cls._dns_cache[host] = ip
                return ip
            except socket.gaierror:
                return None

    @staticmethod
    async def traceroute(
        host: str,
        max_hops: int = 30,
        timeout: int = 2
    ) -> List[Dict[str, Union[int, str, float, None]]]:
        """
        Асинхронная трассировка маршрута до указанного хоста с использованием внешней библиотеки traceroute.

        :param host: Целевой хост (IP или домен)
        :param max_hops: Максимальное количество переходов (hops)
        :param timeout: Таймаут на один запрос (в секундах)
        :return: Список узлов маршрута с информацией об IP и RTT
        """
        logger.debug(f"Начинаем трассировку к {host}, max_hops={max_hops}, timeout={timeout}s")

        try:
            result = await asyncio.to_thread(traceroute, host, max_hops=max_hops, wait=timeout)
        except Exception as e:
            logger.error(f"Ошибка при выполнении traceroute для {host}: {e}")
            return []

        route = []
        for idx, hop in enumerate(result):
            ttl = idx + 1
            ip = hop.get("ip")
            rtt = hop.get("rtt")

            logger.debug(f"Hop {ttl}: {ip or '*'}, RTT: {rtt or '*'} ms")

            route.append({
                "hop": ttl,
                "ip": ip,
                "rtt_ms": round(rtt, 2) if isinstance(rtt, (int, float)) else None
            })

            # Остановить, если достигли цели
            if ip == host or (idx + 1 < len(result) and result[idx + 1].get("ip") == ip):
                logger.info(f"Цель {host} достигнута на hop {ttl}")
                break

        logger.debug(f"Трассировка завершена, маршрут: {route}")
        return route
    @staticmethod
    async def get_owner_info(ip: str) -> Dict[str, Union[str, None]]:
        """
        Получение информации о владельце IP через ipinfo.io.
        """
        import aiohttp

        logger.debug(f"Запрашиваем информацию о владельце для IP: {ip}")
        url = f"http://ipinfo.io/{ip}/json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"Информация получена для {ip}: {data}")
                        return {
                            "ip": ip,
                            "org": data.get("org"),
                            "city": data.get("city"),
                            "region": data.get("region"),
                            "country": data.get("country"),
                            "postal": data.get("postal"),
                            "timezone": data.get("timezone"),
                        }
                    else:
                        logger.warning(f"ipinfo.io вернул статус {resp.status} для {ip}")
        except Exception as e:
            logger.error(f"Ошибка получения данных по {ip}: {e}", exc_info=True)

        logger.debug(f"Не удалось получить данные о владельце для {ip}")
        return {"ip": ip, "org": None, "city": None, "region": None, "country": None}
    @staticmethod
    async def detailed_traceroute(host: str, max_hops: int = 30) -> List[Dict]:
        """
        Трассировка с расширенной информацией (владелец, локация).
        """
        logger.info(f"Выполняем detailed_traceroute для {host}, max_hops={max_hops}")
        route = await NetworkUtils.traceroute(host, max_hops)

        if not route:
            logger.warning(f"Маршрут пустой для {host}")
            return []

        sem = asyncio.Semaphore(10)

        async def fetch_owner(ip: Optional[str]) -> Optional[Dict]:
            if not ip:
                logger.debug("IP не задан, пропускаем запрос владельца")
                return None
            async with sem:
                logger.debug(f"Получаем информацию о владельце для {ip}")
                return await NetworkUtils.get_owner_info(ip)

        tasks = [fetch_owner(hop["ip"]) for hop in route]
        logger.debug(f"Запущено {len(tasks)} задач на получение информации о владельцах")
        owners = await asyncio.gather(*tasks)

        logger.debug(f"Получены данные владельцев: {owners}")

        result = []
        for idx, hop in enumerate(route):
            owner = owners[idx] if idx < len(owners) else None
            result.append({
                "hop": hop["hop"],
                "ip": hop["ip"],
                "rtt_ms": hop["rtt_ms"],
                "org": owner.get("org") if owner else None,
                "location": {
                    "city": owner.get("city") if owner else None,
                    "region": owner.get("region") if owner else None,
                    "country": owner.get("country") if owner else None,
                    "postal": owner.get("postal") if owner else None,
                    "timezone": owner.get("timezone") if owner else None,
                }
            })
            logger.debug(f"Гоп {hop['hop']}: {hop['ip']} — {owner.get('org') if owner else 'Без данных'}")

        logger.info(f"Детальная трассировка завершена для {host}")
        return result
