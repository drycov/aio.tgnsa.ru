import asyncio
import platform
from typing import Callable, List, Awaitable, Optional, Union, Dict, Any
import aiomonitor
import logging
from contextlib import asynccontextmanager
from functools import wraps
import sys
import aiohttp.web_runner
from dataclasses import dataclass
from enum import Enum, auto
from app.core.logging_setup import logger
from app.core.globals import flags

class HookType(Enum):
    STARTUP = auto()
    SHUTDOWN = auto()


@dataclass
class LifecycleHook:
    func: Callable[[], Awaitable[None]]
    name: str
    timeout: Optional[float] = None
    critical: bool = True


import asyncio
import platform
import sys
import time
import importlib.util
from typing import (
    Callable, List, Awaitable, Optional, Union, Dict, Any, AsyncGenerator, Set
)
from contextlib import asynccontextmanager
from functools import wraps
from dataclasses import dataclass
from enum import Enum, auto
import aiomonitor
import aiohttp.web_runner
from app.core.logging_setup import logger
from app.core.globals import flags

# === Новые импорты для метрик и плагинов ===
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    prometheus_available = False
else:
    prometheus_available = True


class HookStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class HookMetrics:
    name: str
    hook_type: str
    start_time: float = 0.0
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: HookStatus = HookStatus.PENDING
    error: Optional[str] = None

    def start(self):
        self.start_time = time.perf_counter()
        self.status = HookStatus.RUNNING

    def finish(self, success: bool, error: Optional[str] = None):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        self.status = HookStatus.SUCCESS if success else HookStatus.FAILED
        self.error = error


class MetricsCollector:
    def __init__(self):
        if not prometheus_available:
            self._enabled = False
            return
        self._enabled = True

        self.hook_duration = Histogram(
            'app_lifecycle_hook_duration_seconds',
            'Duration of lifecycle hooks',
            ['hook_name', 'hook_type', 'status']
        )
        self.hook_total = Counter(
            'app_lifecycle_hook_total',
            'Total number of lifecycle hooks',
            ['hook_name', 'hook_type', 'status']
        )
        self.hooks_running = Gauge(
            'app_lifecycle_hooks_running',
            'Number of currently running hooks',
            ['hook_type']
        )

    def observe_hook(self, metrics: HookMetrics):
        if not self._enabled:
            return
        self.hook_duration.labels(
            hook_name=metrics.name,
            hook_type=metrics.hook_type,
            status=metrics.status.value
        ).observe(metrics.duration or 0)
        self.hook_total.labels(
            hook_name=metrics.name,
            hook_type=metrics.hook_type,
            status=metrics.status.value
        ).inc()

    def inc_running(self, hook_type: str):
        if not self._enabled:
            return
        self.hooks_running.labels(hook_type=hook_type).inc()

    def dec_running(self, hook_type: str):
        if not self._enabled:
            return
        self.hooks_running.labels(hook_type=hook_type).dec()

    def get_metrics(self) -> str:
        if not self._enabled:
            return "# Prometheus not available"
        return generate_latest().decode('utf-8')


class PluginManager:
    def __init__(self, lifecycle_manager):
        self.lifecycle_manager = lifecycle_manager
        self.loaded_plugins: Set[str] = set()

    def load_from_file(self, file_path: str, hook_type: str):
        """Загрузка хуков из внешнего .py файла."""
        spec = importlib.util.spec_from_file_location("plugin", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and hasattr(attr, '_lifecycle_hook'):
                hook_info = attr._lifecycle_hook
                self.lifecycle_manager.add_hook(
                    attr,
                    hook_type=hook_info['hook_type'],
                    name=hook_info['name'],
                    timeout=hook_info['timeout'],
                    critical=hook_info['critical']
                )
                self.loaded_plugins.add(file_path)
                logger.info(f"📦 Loaded hook '{attr_name}' from {file_path}")


def hook_decorator(hook_type: str, name: Optional[str] = None, timeout: Optional[float] = None, critical: bool = True):
    """Декоратор для пометки функций как хуков."""
    def decorator(func):
        func._lifecycle_hook = {
            'hook_type': hook_type,
            'name': name or func.__name__,
            'timeout': timeout,
            'critical': critical
        }
        return func
    return decorator


class HookRegistry:
    """Класс для отслеживания статусов и метрик хуков."""
    def __init__(self):
        self._metrics: Dict[str, HookMetrics] = {}

    def create_metrics(self, name: str, hook_type: str) -> HookMetrics:
        key = f"{hook_type}:{name}"
        metrics = HookMetrics(name=name, hook_type=hook_type)
        self._metrics[key] = metrics
        return metrics

    def get_metrics(self, name: str, hook_type: str) -> Optional[HookMetrics]:
        key = f"{hook_type}:{name}"
        return self._metrics.get(key)

    def get_all_metrics(self) -> List[HookMetrics]:
        return list(self._metrics.values())


class AppLifecycleManager:
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self._startup_hooks: List[LifecycleHook] = []
        self._shutdown_hooks: List[LifecycleHook] = []
        self._monitor: Optional[aiomonitor.Monitor] = None
        self._loop = loop or asyncio.get_event_loop()
        self._startup_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_tasks: Dict[str, asyncio.Task] = {}
        self._is_running = False
        self.debug_mode = flags.debug_mode
        self.logger = logger.bind(component=self.__class__.__name__)

        # === Новые компоненты ===
        self.metrics_collector = MetricsCollector()
        self.hook_registry = HookRegistry()
        self.plugin_manager = PluginManager(self)

        self._patch_aiohttp_for_windows()

    def _patch_aiohttp_for_windows(self) -> None:
        """Patch aiohttp для корректной работы на Windows."""
        if sys.platform.startswith("win"):
            original_init = aiohttp.web_runner.TCPSite.__init__

            def patched_init(
                self,
                runner,
                host=None,
                port=None,
                *,
                shutdown_timeout=60.0,
                backlog=128,
                ssl_context=None,
                reuse_address=None,
                reuse_port=None,
            ):
                return original_init(
                    self,
                    runner,
                    host,
                    port,
                    shutdown_timeout=shutdown_timeout,
                    backlog=backlog,
                    ssl_context=ssl_context,
                    reuse_address=reuse_address,
                    reuse_port=False,
                )

            aiohttp.web_runner.TCPSite.__init__ = patched_init

    def add_hook(
        self,
        func: Callable[[], Awaitable[None]],
        hook_type: str,  # 'startup' или 'shutdown'
        *,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        critical: bool = True,
    ) -> None:
        """Добавить хук программно."""
        hook_name = name or func.__name__
        self.logger.debug(f"➕ Добавлен {hook_type} hook: {hook_name}")
        hook = LifecycleHook(
            func=func, name=hook_name, timeout=timeout, critical=critical
        )
        if hook_type == "startup":
            self._startup_hooks.append(hook)
        else:
            self._shutdown_hooks.append(hook)

    def on_startup(
        self,
        *,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        critical: bool = True,
    ) -> Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]]:
        """Декоратор для регистрации startup-хуков."""
        def decorator(func: Callable[[], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
            self.add_hook(func, "startup", name=name, timeout=timeout, critical=critical)
            return func
        return decorator

    def on_shutdown(
        self,
        *,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        critical: bool = False,
    ) -> Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]]:
        """Декоратор для регистрации shutdown-хуков."""
        def decorator(func: Callable[[], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
            self.add_hook(func, "shutdown", name=name, timeout=timeout, critical=critical)
            return func
        return decorator

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None, None]:
        """Контекстный менеджер жизненного цикла приложения."""
        try:
            await self.startup()
            yield
        except Exception as e:
            self.logger.error("❌ Lifespan error", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def startup(self) -> None:
        """Выполнить все startup-хуки."""
        if self._is_running:
            raise RuntimeError("Application is already running")

        self._is_running = True
        self.logger.info("🟢 Starting application lifecycle")

        if self.debug_mode:
            self.log_active_tasks()

        await self._run_hooks(self._startup_hooks, self._startup_tasks, "startup")
        self.logger.info("🟢 Application started successfully")

    async def shutdown(self) -> None:
        """Выполнить все shutdown-хуки и очистить ресурсы."""
        if not self._is_running:
            return

        self.logger.info("🛑 Shutting down application lifecycle")

        # Отменяем все startup-задачи
        await self._cancel_tasks(self._startup_tasks, "startup")

        # Запускаем shutdown-хуки
        await self._run_hooks(self._shutdown_hooks, self._shutdown_tasks, "shutdown")

        # Отменяем все оставшиеся задачи
        await self._cancel_all_tasks()

        if self._monitor:
            self._monitor.close()
            self._monitor = None

        self._is_running = False
        self.logger.info("🛑 Application shutdown completed")

    async def _run_hooks(
        self,
        hooks: List[LifecycleHook],
        task_dict: Dict[str, asyncio.Task],
        task_prefix: str
    ) -> None:
        """Выполнить хуки параллельно с контролем таймаута и метриками."""
        tasks = []
        for hook in hooks:
            async def run_hook(hook_obj: LifecycleHook):
                # Создаём метрики
                metrics = self.hook_registry.create_metrics(hook_obj.name, task_prefix)
                metrics.start()
                self.metrics_collector.inc_running(task_prefix)

                try:
                    self.logger.info(f"🚀 Running {task_prefix} hook: {hook_obj.name}")
                    if hook_obj.timeout:
                        await asyncio.wait_for(hook_obj.func(), timeout=hook_obj.timeout)
                    else:
                        await hook_obj.func()
                    self.logger.info(f"✅ {task_prefix.capitalize()} hook completed: {hook_obj.name}")
                    metrics.finish(success=True)
                except Exception as e:
                    self.logger.error(
                        f"❌ {task_prefix.capitalize()} hook failed: {hook_obj.name}",
                        exc_info=True
                    )
                    metrics.finish(success=False, error=str(e))
                    if hook_obj.critical:
                        raise
                finally:
                    self.metrics_collector.dec_running(task_prefix)
                    self.metrics_collector.observe_hook(metrics)

            task = asyncio.create_task(run_hook(hook), name=f"{task_prefix}:{hook.name}")
            task_dict[hook.name] = task
            tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    hook = hooks[i]
                    if hook.critical:
                        raise result

    async def _cancel_tasks(
        self,
        tasks: Dict[str, asyncio.Task],
        task_type: str
    ) -> None:
        """Отменить задачи определённого типа."""
        tasks_to_cancel = [t for t in tasks.values() if not t.done()]
        if not tasks_to_cancel:
            return

        self.logger.info(f"⏳ Cancelling {len(tasks_to_cancel)} {task_type} tasks...")
        for task in tasks_to_cancel:
            task.cancel()

        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                timeout=10
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"⚠️ Timeout waiting for {task_type} tasks to cancel")

    async def _cancel_all_tasks(self) -> None:
        """Отменить все активные задачи, кроме текущей."""
        current_task = asyncio.current_task()
        tasks = [
            t
            for t in asyncio.all_tasks(self._loop)
            if t is not current_task and not t.done()
        ]

        if not tasks:
            return

        self.logger.info(f"⏳ Cancelling {len(tasks)} remaining tasks...")
        for task in tasks:
            task.cancel()

        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=15
            )
        except asyncio.TimeoutError:
            self.logger.warning("⚠️ Timeout waiting for tasks to cancel")

    def log_active_tasks(self) -> None:
        """Вывести список активных задач (для отладки)."""
        tasks = asyncio.all_tasks(self._loop)
        self.logger.info(f"🔍 Active tasks: {len(tasks)}")
        for task in tasks:
            self.logger.debug(f"Task: {task.get_name()}, done: {task.done()}")

    # === Новые методы ===

    def get_hook_status(self, name: str, hook_type: str) -> Optional[HookStatus]:
        """Получить статус хука."""
        metrics = self.hook_registry.get_metrics(name, hook_type)
        return metrics.status if metrics else None

    def get_all_hook_metrics(self) -> List[HookMetrics]:
        """Получить все метрики хуков."""
        return self.hook_registry.get_all_metrics()

    def get_prometheus_metrics(self) -> str:
        """Получить метрики в формате Prometheus."""
        return self.metrics_collector.get_metrics()

    def load_plugin(self, file_path: str, hook_type: str):
        """Загрузить хуки из внешнего файла."""
        self.plugin_manager.load_from_file(file_path, hook_type)