import socket
import logging
import platform
import ctypes
import time
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from app.plugins.base import Plugin

logger = logging.getLogger(__name__)


class TracerouteUIPlugin(Plugin):
    name = "traceroute_ui"
    description = "Визуализация traceroute с поддержкой MPLS и расширенной информации"
    priority = 6

    def __init__(self):
        self.router = APIRouter()
        self._config: dict = {}
        self.templates = Jinja2Templates(
            directory=str(Path(__file__).parent / "templates"))

    def init(self, config: dict):
        self._config = config or {}
        base_path = self._config.get("path", "/network/traceroute")

        @self.router.get(base_path)
        async def traceroute_json(
            host: str = Query(...),
            max_hops: Optional[int] = Query(None),
            timeout: Optional[int] = Query(None),
        ):
            result = self.perform_traceroute(
                host,
                max_hops=max_hops or self._config.get("max_hops", 30),
                timeout=timeout or self._config.get("timeout", 2)
            )
            return JSONResponse(result)

        @self.router.get(f"{base_path}/ui")
        async def traceroute_ui(request: Request, host: str = "8.8.8.8"):
            return self.templates.TemplateResponse(
                "traceroute_ui.html",
                {
                    "request": request,
                    "host": host,
                    "static_url": self._config.get("static_url", "/static"),
                    "favicon_url": self._config.get("favicon_url", "/favicon.ico"),
                    "timeout": self._config.get("timeout", 2),
                    "max_hops": self._config.get("max_hops", 30),
                }
            )

    def perform_traceroute(self, host: str, max_hops: int = 30, timeout: int = 2) -> Dict:
        # sourcery skip: low-code-quality
        try:
            from scapy.all import IP, UDP, sr1, conf
        except OSError as e:
            logger.error(f"Scapy error: {e}")
            return {"host": host, "error": str(e)}
        except ImportError as e:
            logger.error(f"Scapy not available: {e}")
            return {"host": host, "error": "Scapy not available in current environment"}

        # Npcap workaround: use WinPcap-compatible mode
        if platform.system() == "Windows":
            try:
                # Принудительно использовать WinPcap-совместимый режим
                conf.use_pcap = True
                # Проверка установки Npcap через поиск winpcap.dll или npcap presence (опционально)
                import subprocess
                output = subprocess.check_output(
                    "where npcap", shell=True, stderr=subprocess.DEVNULL)
            except Exception:
                return {"host": host, "error": "Npcap не установлен или не найден в системном PATH. Установите с опцией 'WinPcap Compatible Mode'."}

        try:
            destination_ip = socket.gethostbyname(host)
        except socket.gaierror as e:
            logger.error(f"Host resolution error: {e}")
            return {"host": host, "error": f"Host resolution failed: {e}"}

        port = 33434
        hops: List[Dict[str, str]] = []

        for ttl in range(1, max_hops + 1):
            pkt = IP(dst=host, ttl=ttl) / UDP(dport=port)

            try:
                reply = sr1(pkt, timeout=timeout, verbose=0)
            except Exception as e:
                logger.exception(f"Error sending packet at ttl={ttl}: {e}")
                hops.append({
                    "hop": str(ttl),
                    "address": "!",
                    "delay": str(e),
                    "mpls": "",
                    "info": "send error"
                })
                break

            hop_info = {
                "hop": str(ttl),
                "address": "*",
                "delay": "timeout",
                "mpls": "",
                "info": ""
            }

            if reply is None:
                hop_info["info"] = "timeout"
            elif reply.haslayer(IP):
                hop_info["address"] = reply.src
                hop_info["delay"] = f"{(reply.time - pkt.sent_time)*1000:.1f} ms" if hasattr(
                    pkt, "sent_time") else ""
                # MPLS parsing
                if reply.haslayer("MPLS"):
                    hop_info["mpls"] = str(reply["MPLS"].label)
                # ICMP Info
                if reply.haslayer("ICMP"):
                    hop_info["info"] = f"ICMP type {reply['ICMP'].type}"
                if reply.type == 3:  # Destination reached
                    hops.append(hop_info)
                    break
            else:
                hop_info["address"] = "?"
                hop_info["info"] = "no IP layer"

            hops.append(hop_info)

        return {
            "host": host,
            "ip": destination_ip,
            "hops": hops,
            "method": "scapy + npcap"
        }

    def register_fastapi(self, app):
        app.include_router(self.router)


plugin = TracerouteUIPlugin()
