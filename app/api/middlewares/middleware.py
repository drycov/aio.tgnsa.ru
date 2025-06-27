import time
from typing import Any, Dict, List, Pattern

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import logger
from app.core.utils.date_utils import isotime


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов с поддержкой исключений."""

    def __init__(
        self,
        app,
        exclude_paths: List[str] = None,
        exclude_patterns: List[Pattern] = None,
    ):
        super().__init__(app)
        self.exclude_paths = set(exclude_paths or [])
        self.exclude_patterns = exclude_patterns or []

    def should_log_request(self, path: str, route_handler) -> bool:
        """Проверяет, нужно ли логировать запрос."""
        if hasattr(route_handler, "skip_logging"):
            return False

        if path in self.exclude_paths:
            return False

        return not any(pattern.match(path) for pattern in self.exclude_patterns)

    def get_request_data(self, request: Request) -> Dict[str, Any]:
        """Собирает базовую информацию о запросе."""
        return {
            "request_id": request.headers.get("X-Request-ID", ""),
            "method": request.method,
            "path": request.url.path,
            "user_agent": request.headers.get("User-Agent", ""),
            "query_params": str(request.query_params),
            "client": request.client.host if request.client else None,
            "timestamp": isotime(),
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Основной обработчик middleware."""
        route_handler = request.scope.get("endpoint")

        if not self.should_log_request(request.url.path, route_handler):
            return await call_next(request)

        start_time = time.time()
        request_data = self.get_request_data(request)

        # Логируем начало запроса с базовой информацией
        # logger.info(
        #     f"→ {request_data['method']} {request_data['path']}",
        #     extra=request_data
        # )

        response = await call_next(request)
        process_time = time.time() - start_time

        # Для завершения добавляем только новую информацию
        logger.info(
            f"{request_data['method']} {request_data['path']} | {response.status_code} | {process_time:.2f}s",
            extra={
                **request_data,
                "status_code": response.status_code,
                "process_time": round(process_time, 3),
            },
        )

        return response
