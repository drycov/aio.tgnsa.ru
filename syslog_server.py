import socketserver

import click
from loguru import logger


class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Получаем данные и логируем сообщение
        data = bytes.decode(self.request[0].strip())
        click.secho(f"Processed syslog message: {data}", fg="green")

class ThreadedSyslogServer(socketserver.ThreadingUDPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "localhost", 514  # Стандартный порт Syslog

    # Запуск многопоточного Syslog сервера
    with ThreadedSyslogServer((HOST, PORT), SyslogUDPHandler) as server:
        click.secho("Syslog server started successfully", fg="green")
        click.secho(f"Listening on {HOST}:{PORT}", fg="yellow")
        server.serve_forever()
