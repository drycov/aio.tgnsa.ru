import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from healthy import Healthy  # Импорт перенесен за пределы класса

httpd = None


class HealthAPIHandler(BaseHTTPRequestHandler):
    # Создаем экземпляр Healthy как атрибут класса
    health_checker = Healthy()

    def do_GET(self):
        # Разбираем URL и проверяем путь запроса
        parsed_path = urlparse(self.path)
        path_segments = parsed_path.path.strip("/").split("/")

        # Endpoint: /health - Получение статусов всех компонентов
        if parsed_path.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = asyncio.run(self.health_checker.get_all_statuses())
            self.wfile.write(json.dumps(response).encode("utf-8"))

        # Endpoint: /health/<component_name> - Получение статуса указанного компонента
        elif len(path_segments) == 2 and path_segments[0] == "health":
            component_name = path_segments[1]
            asyncio.run(self._get_component_status(component_name))

        # Endpoint: /health/report - Получение текстового отчета
        elif parsed_path.path == "/health/report":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"report": self.health_checker.generate_report()}
            self.wfile.write(json.dumps(response).encode("utf-8"))

        # Если запрос не совпадает с поддерживаемыми
        else:
            self.send_error(404, "Endpoint not found")

    async def _get_component_status(self, component_name: str):
        """
        Асинхронный метод, который обрабатывает получение статуса указанного компонента.
        """
        status = await self.health_checker.get_component_status(component_name)
        if status == "NOT_REGISTERED":
            self.send_error(404, "Component not found")
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"component": component_name, "status": status}
            self.wfile.write(json.dumps(response).encode("utf-8"))


def run(server_class=HTTPServer, handler_class=HealthAPIHandler, port=8000):
    """
    Запуск HTTP-сервера для Health API в отдельном потоке.
    """
    global httpd
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Health API server running on port {port}")

    # Запускаем сервер в отдельном потоке, чтобы основной поток оставался свободным
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.start()


def stop_server():
    """
    Остановка HTTP-сервера, если он активен.
    """
    global httpd
    if httpd:
        print("Stopping Health API server...")
        httpd.shutdown()
        httpd.server_close()
        httpd = None  # Очищаем переменную, чтобы показать, что сервер остановлен
        print("Health API server stopped.")
    else:
        print("Health API server is not running.")
