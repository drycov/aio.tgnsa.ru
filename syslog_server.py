import socketserver
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import click
from loguru import logger
from sqlalchemy.orm import declarative_base

# Инициализация базы данных
DATABASE_URL = "sqlite:///syslog.db"  # Укажите путь к базе данных
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)  # Установите echo=True для логов SQL-запросов
Session = sessionmaker(bind=engine)


# Определение модели для таблицы логов
class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Создаём таблицу, если её нет
Base.metadata.create_all(engine)


# Класс обработчика сообщений Syslog
class SyslogUDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # Получаем данные из запроса
        data = bytes.decode(self.request[0].strip())
        logger.info(f"Received syslog message: {data}")

        # Сохраняем сообщение в базу данных
        self.save_to_db(data)

    @staticmethod
    def save_to_db(message):
        """Сохраняет сообщение в базу данных."""
        session = Session()
        try:
            log_entry = Log(message=message)
            session.add(log_entry)
            session.commit()
            logger.info("Syslog message saved to database.")
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            session.rollback()
        finally:
            session.close()


# Класс многопоточного Syslog-сервера
class ThreadedSyslogServer(socketserver.ThreadingUDPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "localhost", 514  # Стандартный порт Syslog

    # Запуск сервера
    with ThreadedSyslogServer((HOST, PORT), SyslogUDPHandler) as server:
        click.secho("Syslog server started successfully", fg="green")
        click.secho(f"Listening on {HOST}:{PORT}", fg="yellow")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            click.secho("Server shutting down...", fg="red")
