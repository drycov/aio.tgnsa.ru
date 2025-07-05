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
from app.core.config import debug_mode
from app.core.logging_setup import configure_logger



class HookType(Enum):
    STARTUP = auto()
    SHUTDOWN = auto()


@dataclass
class LifecycleHook:
    func: Callable[[], Awaitable[None]]
    name: str
    timeout: Optional[float] = None
    critical: bool = True


class AppLifecycleManager:
    name="AppLifecycleManager"
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self._startup_hooks: List[LifecycleHook] = []
        self._shutdown_hooks: List[LifecycleHook] = []
        self._monitor: Optional[aiomonitor.Monitor] = None
        self._loop = loop or asyncio.get_event_loop()
        self._startup_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_tasks: Dict[str, asyncio.Task] = {}
        self.logger = configure_logger().bind(component=f"{__class__.__name__}")
        self._is_running = False

        self._patch_aiohttp_for_windows()

    def _patch_aiohttp_for_windows(self) -> None:
        """Patch aiohttp for correct operation on Windows."""
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

    def on_startup(
        self,
        *,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        critical: bool = True,
    ) -> Union[
        Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]],
        Callable[[], Awaitable[None]],
    ]:
        """Decorator to register startup hooks."""

        def decorator(
            func: Callable[[], Awaitable[None]],
        ) -> Callable[[], Awaitable[None]]:
            hook_name = name or func.__name__

            @wraps(func)
            async def wrapped():
                try:
                    self.logger.info(f"🚀 Running startup hook: {hook_name}")
                    if timeout:
                        await asyncio.wait_for(func(), timeout=timeout)
                    else:
                        await func()
                    self.logger.info(f"✅ Startup hook completed: {hook_name}")
                except Exception as e:
                    self.logger.error(f"❌ Startup hook failed: {hook_name}: {str(e)}")
                    if critical:
                        raise

            self._startup_hooks.append(
                LifecycleHook(
                    func=wrapped, name=hook_name, timeout=timeout, critical=critical
                )
            )
            return wrapped

        return decorator

    def on_shutdown(
        self,
        *,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        critical: bool = False,
    ) -> Union[
        Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]],
        Callable[[], Awaitable[None]],
    ]:
        """Decorator to register shutdown hooks."""

        def decorator(
            func: Callable[[], Awaitable[None]],
        ) -> Callable[[], Awaitable[None]]:
            hook_name = name or func.__name__

            @wraps(func)
            async def wrapped():
                try:
                    self.logger.info(f"🛑 Running shutdown hook: {hook_name}")
                    if timeout:
                        await asyncio.wait_for(func(), timeout=timeout)
                    else:
                        await func()
                    self.logger.info(f"✅ Shutdown hook completed: {hook_name}")
                except Exception as e:
                    self.logger.error(f"❌ Shutdown hook failed: {hook_name}: {str(e)}")
                    if critical:
                        raise

            self._shutdown_hooks.append(
                LifecycleHook(
                    func=wrapped, name=hook_name, timeout=timeout, critical=critical
                )
            )
            return wrapped

        return decorator

    @asynccontextmanager
    async def lifespan(self):
        """Context manager to manage the application lifecycle."""
        try:
            await self.startup()
            yield
        except Exception as e:
            self.logger.error(f"❌ Lifespan failed: {str(e)}")
        finally:
            await self.shutdown()

    async def startup(self) -> None:
        """Run all startup hooks."""
        if self._is_running:
            raise RuntimeError("Application is already running")

        self._is_running = True
        self.logger.info("🟢 Starting application lifecycle")

        if debug_mode:
            self._start_monitor()

        for hook in self._startup_hooks:
            task = asyncio.create_task(hook.func(), name=f"startup:{hook.name}")
            self._startup_tasks[hook.name] = task

        await asyncio.gather(*self._startup_tasks.values(), return_exceptions=False)
        self.logger.info("🟢 Application started successfully")

    async def shutdown(self) -> None:
        """Run all shutdown hooks and clean up resources."""
        if not self._is_running:
            return

        self.logger.info("🛑 Shutting down application lifecycle")

        # Cancel all startup tasks
        await self._cancel_tasks(self._startup_tasks, "startup")

        # Run shutdown hooks
        for hook in self._shutdown_hooks:
            task = asyncio.create_task(hook.func(), name=f"shutdown:{hook.name}")
            self._shutdown_tasks[hook.name] = task

        try:
            await asyncio.wait_for(
                asyncio.gather(*self._shutdown_tasks.values(), return_exceptions=True),
                timeout=30,
            )
        except asyncio.TimeoutError:
            self.logger.warning("⚠️ Timeout waiting for shutdown hooks to complete")

        # Cancel remaining tasks
        await self._cancel_all_tasks()

        if self._monitor:
            self._monitor.close()
            self._monitor = None

        self._is_running = False
        self.logger.info("🛑 Application shutdown completed")

    def _start_monitor(self) -> None:
        """
        Безопасно запускает aiomonitor, адаптируясь к платформе.
        На Windows отключает telnet-сервер, т.к. ProactorEventLoop не поддерживает add_reader.
        """
        try:
            is_windows = (
                sys.platform.startswith("win") or platform.system() == "Windows"
            )
            self._monitor = aiomonitor.start_monitor(
                loop=self._loop,
                console_port=50101,
                console_enabled=not is_windows,
            )
            self.logger.info(
                "🔧 aiomonitor started (telnet enabled: %s)",
                not is_windows,
            )
        except NotImplementedError as nie:
            self.logger.warning(
                "⚠️ aiomonitor telnet disabled (platform limitation): %s", nie
            )
        except Exception as e:
            self.logger.exception("❌ Failed to start aiomonitor: %s", e)

    async def _cancel_tasks(
        self, tasks: Dict[str, asyncio.Task], task_type: str
    ) -> None:
        """Cancel tasks of a specific type."""
        tasks_to_cancel = [t for t in tasks.values() if not t.done()]
        if not tasks_to_cancel:
            return

        self.logger.info(f"⏳ Cancelling {len(tasks_to_cancel)} {task_type} tasks...")
        for task in tasks_to_cancel:
            task.cancel()

        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks_to_cancel, return_exceptions=True), timeout=10
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"⚠️ Timeout waiting for {task_type} tasks to cancel")

    async def _cancel_all_tasks(self) -> None:
        """Cancel all active tasks except the current one."""
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
                asyncio.gather(*tasks, return_exceptions=True), timeout=15
            )
        except asyncio.TimeoutError:
            self.logger.warning("⚠️ Timeout waiting for tasks to cancel")

    def log_active_tasks(self) -> None:
        """Log information about current tasks."""
        tasks = asyncio.all_tasks(self._loop)
        self.logger.info(f"🔍 Active tasks: {len(tasks)}")
        for task in tasks:
            self.logger.debug(f"Task: {task.get_name()}, done: {task.done()}")
