import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse, parse_qs

from app.utils.logger_instance import app_logger
from healthy import Healthy  # Импортируем класс Healthy


class HealthAPIHandler(BaseHTTPRequestHandler):
    health_checker = Healthy()

    def _send_response(self, status_code: int, data: Any, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        if isinstance(data, dict):
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            self.wfile.write(data.encode("utf-8"))

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path_segments = parsed_path.path.strip("/").split("/")
        try:
            if parsed_path.path == "/admin":
                # Рендерим HTML-админку
                self._send_response(200, self.render_admin_page(), content_type="text/html")
            elif parsed_path.path == "/health":
                statuses = asyncio.run(self.health_checker.get_all_statuses())
                self._send_response(200, statuses)
            elif parsed_path.path == "/health/report":
                query = parsed_path.query
                if query == "json":
                    report = asyncio.run(self.health_checker.generate_report())
                    self._send_response(200, report, content_type="application/json")
                else:
                    report = asyncio.run(self.health_checker.generate_html_report())
                    self._send_response(200, report, content_type="text/html")
            elif len(path_segments) == 2 and path_segments[0] == "health":
                component_name = path_segments[1]
                status = asyncio.run(self.health_checker.get_component_status(component_name))
                if status == "NOT_REGISTERED":
                    self._send_response(404, {"error": "Component not found"})
                else:
                    self._send_response(200, {"component": component_name, "status": status})
            else:
                self._send_response(404, {"error": "Invalid endpoint"})
        except Exception as e:
            self._send_response(500, {"error": "Internal server error", "details": str(e)})

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path_segments = parsed_path.path.strip("/").split("/")
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = parse_qs(post_data.decode("utf-8"))

        try:
            if parsed_path.path == "/admin/action":
                action = data.get("action", [""])[0]
                if action == "reload":
                    asyncio.run(self.health_checker.perform_health_checks())
                    self._send_response(200, {"message": "Health checks reloaded"})
                else:
                    self._send_response(400, {"error": "Invalid action"})
            else:
                self._send_response(404, {"error": "Invalid endpoint"})
        except Exception as e:
            self._send_response(500, {"error": "Internal server error", "details": str(e)})

    def render_admin_page(self) -> str:
        """
        Возвращает HTML для админки.
        """
        statuses = asyncio.run(self.health_checker.get_all_statuses())
        rows = "".join(
            f"<tr><td>{name}</td><td>{status}</td></tr>"
            for name, status in statuses.items()
        )
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Panel</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f4f4f4; }}
            </style>
        </head>
        <body>
            <h1>Admin Panel</h1>
            <form method="POST" action="/admin/action">
                <button type="submit" name="action" value="reload">Reload Health Checks</button>
            </form>
            <h2>Component Status</h2>
            <table>
                <thead>
                    <tr>
                        <th>Component</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        </html>
        """


def run(server_class=HTTPServer, handler_class=HealthAPIHandler, port=8000):
    global httpd
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    app_logger.info(f"Health API server running on port {port}")
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()


def stop_server():
    global httpd
    if httpd:
        app_logger.warning("Stopping Health API server...")
        httpd.shutdown()
        httpd.server_close()
        httpd = None
        app_logger.info("Health API server stopped.")
    else:
        app_logger.error("Health API server is not running.")
