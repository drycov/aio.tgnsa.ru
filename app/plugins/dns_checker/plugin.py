import asyncio
import socket
import platform

import psutil
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.plugins.base import Plugin


class DNSCheckerPlugin(Plugin):
    name = "dns_checker"
    description = "Проверка DNS-записей, шлюзов, ping и интерфейсов"
    priority = 6

    def __init__(self):
        self.router = APIRouter()
        self._config = {}
        self.healthcheck = None

    def init(self, config: dict):
        self._config = config or {}
        path = self._config.get("path", "/network/dns")

        @self.router.get(f"{path}")
        async def check_dns(domain: str = Query(...)):
            return await self.resolve_domain(domain)

        @self.router.get(f"{path}/interfaces")
        async def interfaces():
            return self.get_interfaces()

        @self.router.get(f"{path}/ping")
        async def ping(host: str = Query(...)):
            return await self.ping_host(host)

        @self.router.get(f"{path}/gateways")
        async def check_gateways():
            return await self.ping_gateways()

    def register_fastapi(self, app):
        app.include_router(self.router)

    def register_healthcheck(self, hc_plugin: Plugin):
        """Регистрация проверки DNS и шлюзов как optional probe."""
        self.healthcheck = hc_plugin

        async def dns_gateway_probe() -> bool:
            try:
                domain = self._config.get("health_domain", "google.com")
                result = await self.resolve_domain(domain)
                resolved = result.get("resolved", [])
                if not resolved:
                    return False

                gateway_ping = await self.ping_gateways()
                return all(r.get("returncode", 1) == 0 for r in gateway_ping)
            except Exception:
                return False

        if hasattr(hc_plugin, "register_probe"):
            hc_plugin.register_probe("dns_probe", dns_gateway_probe, group="optional")
        else:
            hc_plugin.register_fastapi_probe(
                "dns_probe", dns_gateway_probe, group="optional"
            )

    async def resolve_domain(self, domain: str):
        try:
            result = await asyncio.get_event_loop().getaddrinfo(domain, None)
            addresses = list({addr[-1][0] for addr in result})
            return {"domain": domain, "resolved": addresses}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    def get_interfaces(self):
        return {
            name: [
                addr.address
                for addr in addrs
                if addr.family in (socket.AF_INET, socket.AF_INET6)
            ]
            for name, addrs in psutil.net_if_addrs().items()
        }

    async def ping_host(self, host: str, count: int = 2):
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", str(count), host]
        else:
            cmd = ["ping", "-c", str(count), host]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            def safe_decode(data: bytes) -> str:
                for encoding in ("utf-8", "cp866", "windows-1251", "latin-1"):
                    try:
                        return data.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                return data.decode("utf-8", errors="replace")

            return {
                "host": host,
                "returncode": proc.returncode,
                "output": safe_decode(stdout),
                "error": safe_decode(stderr) if stderr else None,
            }

        except Exception as e:
            return {"host": host, "error": str(e)}

    async def ping_gateways(self):
        gateways = self._config.get("gateways", ["8.8.8.8", "1.1.1.1"])
        results = []
        for gw in gateways:
            result = await self.ping_host(gw)
            results.append(result)
        return results

    async def health_probe(self) -> dict:
        """Проверка DNS и шлюзов для интеграции в healthcheck."""
        test_domain = self._config.get("health_domain", "google.com")
        dns_result = await self.resolve_domain(test_domain)
        gateway_result = await self.ping_gateways()

        return {
            "dns": dns_result,
            "gateways": gateway_result,
        }


plugin = DNSCheckerPlugin()
