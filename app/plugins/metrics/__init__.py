import threading
import time
import logging
from prometheus_client import (
    Gauge, Counter, Histogram, CollectorRegistry, start_http_server
)

from app.plugins.base import Plugin
from app.core.config import logger  # корпоративный логгер


class MetricsPlugin(Plugin):
    name = "metrics"
    description = "Экспозиция Prometheus-метрик с интеграцией FastAPI и aiogram"
    priority = 0

    _running: bool = False
    _thread: threading.Thread | None = None

    def __init__(self):
        self._config = {}
        self._registry = CollectorRegistry()

        # FastAPI метрики
        self.http_requests_total = Counter(
            "http_requests_total",
            "Общее количество HTTP запросов",
            ["method", "endpoint", "status_code"],
            registry=self._registry,
        )
        self.http_request_duration = Histogram(
            "http_request_duration_seconds",
            "Время обработки HTTP запроса",
            ["endpoint"],
            registry=self._registry,
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        )
        self.in_progress_requests = Gauge(
            "in_progress_requests",
            "Количество одновременных активных HTTP запросов",
            registry=self._registry,
        )
        self.http_errors_total = Counter(
            "http_errors_total",
            "Количество HTTP ошибок",
            ["status_code"],
            registry=self._registry,
        )

        # aiogram метрики
        self.telegram_updates_received = Counter(
            "telegram_updates_received_total",
            "Количество полученных Telegram апдейтов",
            registry=self._registry,
        )
        self.telegram_updates_handled = Counter(
            "telegram_updates_handled_total",
            "Количество обработанных Telegram апдейтов",
            registry=self._registry,
        )
        self.telegram_handlers_errors = Counter(
            "telegram_handlers_errors_total",
            "Количество ошибок в Telegram обработчиках",
            registry=self._registry,
        )
        self.telegram_update_processing_duration = Histogram(
            "telegram_update_processing_duration_seconds",
            "Время обработки Telegram апдейта",
            registry=self._registry,
        )
        self.telegram_task_queue_length = Gauge(
            "telegram_task_queue_length",
            "Длина очереди задач aiogram",
            registry=self._registry,
        )

        self._port: int = 8001

    def init(self, config: dict):
        self._config = config or {}
        self._port = self._config.get("port", 8001)

        self._running = True
        try:
            start_http_server(self._port, registry=self._registry)
            logger.info(f"Metrics HTTP server started on port {self._port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus metrics server: {e}")
            raise

        self._thread = threading.Thread(target=self._run_metrics_loop, daemon=True)
        self._thread.start()

    def _run_metrics_loop(self):
        logger.info("Metrics loop started")
        while self._running:
            try:
                self._update_internal_metrics()
            except Exception as e:
                logger.error(f"Error updating internal metrics: {e}")
            time.sleep(10)  # Обновление метрик по расписанию
        logger.info("Metrics loop stopped")

    def _update_internal_metrics(self):
        # Например, можно собирать данные по системным ресурсам
        import psutil
        # cpu и память процессора
        cpu_percent = psutil.cpu_percent()
        mem_rss = psutil.Process().memory_info().rss

        # Можно добавить кастомные Gauge для них, если нужно
        # Или логировать/отправлять их в другую систему

        logger.debug(f"CPU usage: {cpu_percent}%, Memory RSS: {mem_rss} bytes")

    def register_fastapi(self, app):
        """Регистрация middleware FastAPI для сбора метрик HTTP запросов."""

        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from starlette.responses import Response
        import time

        plugin = self

        class PrometheusMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                plugin.in_progress_requests.inc()
                start_time = time.time()
                try:
                    response: Response = await call_next(request)
                    status_code = response.status_code
                    plugin.http_requests_total.labels(
                        method=request.method,
                        endpoint=request.url.path,
                        status_code=str(status_code)
                    ).inc()
                    if status_code >= 400:
                        plugin.http_errors_total.labels(
                            status_code=str(status_code)
                        ).inc()
                except Exception as e:
                    plugin.http_errors_total.labels(status_code="500").inc()
                    raise e
                finally:
                    duration = time.time() - start_time
                    plugin.http_request_duration.labels(endpoint=request.url.path).observe(duration)
                    plugin.in_progress_requests.dec()
                return response

        app.add_middleware(PrometheusMiddleware)

    def register_aiogram(self, dispatcher, queue=None):
        """Интеграция с aiogram: обертки для сбора метрик."""

        plugin = self

        original_process_update = dispatcher.process_update

        async def wrapped_process_update(update, *args, **kwargs):
            plugin.telegram_updates_received.inc()
            start_time = time.time()
            try:
                result = await original_process_update(update, *args, **kwargs)
                plugin.telegram_updates_handled.inc()
                return result
            except Exception:
                plugin.telegram_handlers_errors.inc()
                raise
            finally:
                duration = time.time() - start_time
                plugin.telegram_update_processing_duration.observe(duration)

        dispatcher.process_update = wrapped_process_update

        # Если есть очередь задач - можно обновлять длину очереди по расписанию
        if queue:
            import asyncio

            async def monitor_queue_length():
                while plugin._running:
                    plugin.telegram_task_queue_length.set(queue.qsize())
                    await asyncio.sleep(10)

            import asyncio
            asyncio.create_task(monitor_queue_length())

    def shutdown(self):
        if self._running:
            logger.info("Shutting down MetricsPlugin...")
            self._running = False
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=10)
            logger.info("MetricsPlugin shutdown complete")


plugin = MetricsPlugin()
