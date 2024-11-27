import configparser
import os

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox


class ConnectionWindow(QMainWindow):
    CONFIG_FILE = "config.ini"

    def __init__(self, start_main_app_callback):
        super().__init__()
        self.start_main_app_callback = start_main_app_callback
        self.setWindowTitle("Настройка сервера")
        self.setGeometry(100, 100, 400, 200)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Поле для ввода Endpoint
        self.endpoint_input = QLineEdit(self)
        self.endpoint_input.setPlaceholderText("Введите endpoint сервера (например, http://127.0.0.1)")
        self.layout.addWidget(self.endpoint_input)

        # Поле для ввода порта
        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText("Введите порт (например, 8000)")
        self.layout.addWidget(self.port_input)

        # Кнопка для сохранения и перехода к основному приложению
        self.start_button = QPushButton("Запустить приложение", self)
        self.start_button.clicked.connect(self.validate_and_start_app)
        self.layout.addWidget(self.start_button)

        # Загрузка конфигурации
        self.load_config()

    def validate_and_start_app(self):
        endpoint = self.endpoint_input.text()
        port = self.port_input.text()

        if not endpoint or not port.isdigit():
            QMessageBox.warning(self, "Ошибка ввода", "Пожалуйста, укажите корректный endpoint и порт.")
            return

        # Сохранение конфигурации
        self.save_config(endpoint, port)

        # Запуск основного приложения
        self.start_main_app_callback(endpoint, port)
        self.close()

    def load_config(self):
        """Загрузка последней сессии из файла конфигурации."""
        if not os.path.exists(self.CONFIG_FILE):
            return

        config = configparser.ConfigParser()
        config.read(self.CONFIG_FILE)

        if "Server" in config:
            self.endpoint_input.setText(config["Server"].get("Endpoint", ""))
            self.port_input.setText(config["Server"].get("Port", ""))

    def save_config(self, endpoint, port):
        """Сохранение текущих данных в файл конфигурации."""
        config = configparser.ConfigParser()
        config["Server"] = {"Endpoint": endpoint, "Port": port}

        with open(self.CONFIG_FILE, "w") as configfile:
            config.write(configfile)
