import inspect
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, List, Literal, Tuple, Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse

from app.plugins.base import Plugin

ProbeFn = Callable[[], Union[bool, Awaitable[bool]]]
ProbeGroup = Literal["critical", "optional"]
SystemStatus = Literal[
    "OK", "DEGRADED", "FAIL", "SHUTDOWN", "UNKNOWN", "MAINTENANCE", "INIT"
]


class HealthCheckPlugin(Plugin):
    name = "healthcheck"
    description = "Expose health/liveness/readiness endpoints for monitoring"
    priority = 0  # Should load early to catch startup issues

    def __init__(self):
        self.router = APIRouter()
        self._config: Dict = {}
        self._start_time = datetime.now(timezone.utc)

        # Core system states
        self._alive: bool = True
        self._ready: bool = False  # Starts as not ready until initialization completes
        self._status: SystemStatus = "INIT"

        # Probe management
        self._probes: Dict[ProbeGroup, List[Tuple[str, ProbeFn]]] = {
            "critical": [],
            "optional": [],
        }
        self._last_success: Dict[str, float] = {}
        self._last_failure: Dict[str, Tuple[float, str]] = {}

    def register_probe(self, name: str, fn: ProbeFn, group: ProbeGroup = "critical"):
        """Register a new health check probe."""
        if not callable(fn):
            raise ValueError("Probe must be callable")
        self._probes[group].append((name, fn))

        if self._status == "INIT" and group == "critical":
            self._status = "DEGRADED"  # System is partially initialized

    def set_alive(self, value: bool = True):
        """Set the basic liveness state."""
        self._alive = value
        self._update_aggregate_status()

    def set_ready(self, value: bool = True):
        """Set the readiness state."""
        self._ready = value
        self._update_aggregate_status()

    def set_status(self, status: SystemStatus):
        """Set the overall system status."""
        allowed: List[SystemStatus] = [
            "OK",
            "DEGRADED",
            "FAIL",
            "SHUTDOWN",
            "UNKNOWN",
            "MAINTENANCE",
            "INIT",
        ]
        if status not in allowed:
            raise ValueError(f"Invalid status '{status}'. Allowed: {allowed}")

        self._status = status
        if hasattr(self, "logger"):
            self.logger.info(f"[healthcheck] System status changed to: {status}")

    def _update_aggregate_status(self):
        """Automatically update status based on component states."""
        if not self._alive:
            self._status = "FAIL"
        elif not self._ready:
            self._status = "DEGRADED"
        elif self._status in ["INIT", "DEGRADED"]:
            self._status = "OK"

    def init(self, config: dict):
        """Initialize the plugin with configuration."""
        self._config = config or {}
        base_path = self._config.get("path", "/health")

        # Auto-integrate common services
        self._auto_register_probes()

        # Core health endpoints
        @self.router.get(f"{base_path}")
        async def base_health():
            return JSONResponse(
                {
                    "status": self._status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        @self.router.get(f"{base_path}/liveness")
        async def liveness_check():
            return JSONResponse(
                {"alive": self._alive, "status": self._status},
                status_code=200 if self._alive else 503,
            )

        @self.router.get(f"{base_path}/readiness")
        async def readiness_check():
            return JSONResponse(
                {"ready": self._ready, "status": self._status},
                status_code=200 if self._ready else 503,
            )

        @self.router.get(f"{base_path}/details")
        async def detailed_status():
            return JSONResponse(
                {
                    "status": self._status,
                    "alive": self._alive,
                    "ready": self._ready,
                    "started_at": self._start_time.isoformat(),
                    "uptime_seconds": (
                        datetime.now(timezone.utc) - self._start_time
                    ).total_seconds(),
                    "probe_counts": {
                        "critical": len(self._probes["critical"]),
                        "optional": len(self._probes["optional"]),
                    },
                }
            )

        @self.router.get(f"{base_path}/probes")
        async def probes_status():
            """Detailed probe status that automatically updates system status."""
            result = {
                "timestamp": time.time(),
                "status": "OK",
                "groups": {},
                "critical_failures": 0,
            }

            for group, checks in self._probes.items():
                group_results = {}
                for name, check_fn in checks:
                    probe_result = await self._run_probe(name, check_fn)
                    group_results[name] = probe_result

                    if not probe_result["ok"] and group == "critical":
                        result["critical_failures"] += 1

                result["groups"][group] = group_results

            # Update system status based on probe results
            if result["critical_failures"] > 0:
                self.set_status("DEGRADED" if self._ready else "FAIL")
                result["status"] = "DEGRADED"
            else:
                self.set_status("OK")
                result["status"] = "OK"

            return JSONResponse(
                result, status_code=200 if result["status"] == "OK" else 503
            )

        @self.router.get(f"{base_path}/metrics", include_in_schema=False)
        async def metrics():
            metrics = [
                f'health_status{{state="{self._status}"}} 1',
                f'probes_total{{group="critical"}} {len(self._probes["critical"])}',
                f'probes_total{{group="optional"}} {len(self._probes["optional"])}',
            ]
            return PlainTextResponse("\n".join(metrics), media_type="text/plain")

        # Mark system as ready after successful initialization
        self.set_ready(True)
        self.set_status("OK")

    async def _run_probe(self, name: str, check_fn: ProbeFn) -> Dict:
        """Execute a single probe and record results."""
        try:
            result = check_fn()
            if inspect.isawaitable(result):
                result = await result
            if inspect.iscoroutinefunction(check_fn):
                result = await check_fn()

            success = bool(result)
            if success:
                self._last_success[name] = time.time()
            else:
                self._last_failure[name] = (time.time(), "Probe returned False")

            return {
                "ok": success,
                "last_success": self._last_success.get(name),
                "last_failure": self._last_failure.get(name, [None, None])[0],
            }
        except Exception as e:
            self._last_failure[name] = (time.time(), str(e))
            return {
                "ok": False,
                "error": str(e),
                "last_success": self._last_success.get(name),
                "last_failure": time.time(),
            }

    def _auto_register_probes(self):
        """Auto-register probes for common services from config."""
        # Redis integration
        if redis := self._config.get("redis_client"):
            self.register_probe("redis_ping", lambda: redis.ping(), group="critical")

        # Database integration
        if db := self._config.get("db_client"):

            async def db_check():
                try:
                    await db.execute("SELECT 1")
                    return True
                except Exception:
                    return False

            self.register_probe("db_connect", db_check, group="critical")

    def register_fastapi(self, app):
        """Register routes and lifecycle handlers."""
        app.include_router(self.router)

        # Startup handler - mark system as ready
        @app.on_event("startup")
        async def startup_handler():
            self.set_alive(True)
            self.set_ready(True)
            self.set_status("OK")
            if hasattr(self, "logger"):
                self.logger.info("[healthcheck] System marked as ready")

        # Shutdown handler - mark system as shutting down
        @app.on_event("shutdown")
        async def shutdown_handler():
            self.set_alive(False)
            self.set_ready(False)
            self.set_status("SHUTDOWN")
            if hasattr(self, "logger"):
                self.logger.info("[healthcheck] System shutdown initiated")

        # Maintenance mode example (could be triggered via API)
        @app.get("/admin/maintenance", include_in_schema=False)
        async def enter_maintenance():
            self.set_status("MAINTENANCE")
            self.set_ready(False)
            return {"status": "MAINTENANCE mode activated"}


plugin = HealthCheckPlugin()
