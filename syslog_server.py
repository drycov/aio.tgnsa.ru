import socketserver
import sqlite3
import click
from loguru import logger


# Класс обработчика сообщений Syslog
class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Получаем данные из запроса
        data = bytes.decode(self.request[0].strip())
        # Логируем сообщение
        logger.info(f"Received syslog message: {data}")
        # click.secho(f"Processed syslog message: {data}", fg="green")

        # Сохраняем сообщение в базу данных
        self.save_to_db(data)

    def save_to_db(self, message):
        """Сохраняет сообщение в базу данных."""
        conn = sqlite3.connect("syslog.db")  # Соединяемся с базой
        cursor = conn.cursor()

        # Вставляем сообщение в таблицу
        cursor.execute("INSERT INTO logs (message) VALUES (?)", (message,))
        conn.commit()  # Сохраняем изменения
        conn.close()  # Закрываем соединение


# Класс многопоточного Syslog-сервера
class ThreadedSyslogServer(socketserver.ThreadingUDPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "localhost", 514  # Стандартный порт Syslog

    # Создаём таблицу, если её нет
    conn = sqlite3.connect("syslog.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    # Запуск сервера
    with ThreadedSyslogServer((HOST, PORT), SyslogUDPHandler) as server:
        click.secho("Syslog server started successfully", fg="green")
        click.secho(f"Listening on {HOST}:{PORT}", fg="yellow")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            click.secho("Server shutting down...", fg="red")
