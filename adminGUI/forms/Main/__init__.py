import json

import httpx
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QMessageBox, QLabel, QTreeWidgetItem, QFileDialog,
    QTreeWidget, QDialog, QFormLayout, QCheckBox, QAbstractItemView, QHBoxLayout, QSpacerItem, QSizePolicy,
    QInputDialog, QAction, QToolBar
)


def api_request(method: str, url: str, headers: dict = None, data: dict = None, json_data: dict = None):
    """
    Универсальный метод для отправки запросов к API.
    """
    try:
        with httpx.Client() as client:
            response = client.request(method, url, headers=headers, data=data, json=json_data)
            response.raise_for_status()
            return response
    except httpx.RequestError as e:
        raise RuntimeError(f"Ошибка запроса: {e}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Ошибка статуса: {e}")


class BaseTab(QWidget):
    """
    Базовый класс для всех вкладок.
    """

    def __init__(self, api_base_url: str, token: str, parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.token = token

    def handle_exception(self, action: str, exception: Exception):
        """
        Унифицированная обработка исключений.
        """
        QMessageBox.critical(self, "Ошибка", f"Не удалось {action}:\n{exception}")


class LoginDialog(QDialog):
    def __init__(self, api_base_url, parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.setWindowTitle("Авторизация")
        self.setGeometry(300, 200, 400, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Поля для логина и пароля
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)

        # Кнопки "Войти" и "Отмена"
        buttons_layout = QHBoxLayout()
        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.authenticate)
        buttons_layout.addWidget(login_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def authenticate(self):
        """
        Отправляет логин и пароль на сервер для получения токена.
        """
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль.")
            return

        try:
            url = f"{self.api_base_url}/login"
            response = api_request("POST", url, json_data={"userid": login, "password": password}
                                   )
            response.raise_for_status()

            data = response.json()
            token = data.get("access_token")

            if token:
                # Сохранение токена в настройках
                settings = QSettings("config.ini", QSettings.IniFormat)
                settings.setValue("auth/token", token)
                settings.setValue("auth/userid", self.login_input.text())
                settings.setValue("auth/password", self.password_input.text())

                settings.sync()

                QMessageBox.information(self, "Успех", "Успешная авторизация!")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Токен не получен.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось авторизоваться:\n{e}")


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(500)
        self.settings = QSettings("config.ini", QSettings.IniFormat)  # Объект для работы с INI-файлом

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Создаем вкладки
        self.tabs = QTabWidget()

        # Вкладка API
        self.api_tab = self.create_api_tab()
        self.tabs.addTab(self.api_tab, "API")

        # Вкладка Данные
        self.data_tab = self.create_data_tab()
        self.tabs.addTab(self.data_tab, "Данные")

        # Вкладка Система
        self.system_tab = self.create_system_tab()
        self.tabs.addTab(self.system_tab, "Система")

        layout.addWidget(self.tabs)

        # Кнопки сохранения и отмены
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.close)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def create_api_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.api_endpoint_input = QLineEdit()
        self.api_endpoint_input.setPlaceholderText("Введите API Endpoint")
        self.api_endpoint_input.setText(self.settings.value("api/endpoint", ""))
        layout.addWidget(QLabel("API Endpoint:"))
        layout.addWidget(self.api_endpoint_input)

        self.api_port_input = QLineEdit()
        self.api_port_input.setPlaceholderText("Введите API Port")
        self.api_port_input.setText(self.settings.value("api/port", ""))
        layout.addWidget(QLabel("API Port:"))
        layout.addWidget(self.api_port_input)

        tab.setLayout(layout)
        return tab

    def create_data_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.data_path_input = QLineEdit()
        self.data_path_input.setPlaceholderText("Выберите путь к данным")
        self.data_path_input.setText(self.settings.value("data/path", ""))
        layout.addWidget(QLabel("Путь к данным:"))
        layout.addWidget(self.data_path_input)

        browse_button = QPushButton("Обзор...")
        browse_button.clicked.connect(self.browse_data_path)
        layout.addWidget(browse_button)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        tab.setLayout(layout)
        return tab

    def create_system_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.default_timezone_input = QLineEdit()
        self.default_timezone_input.setPlaceholderText("Введите часовой пояс")
        self.default_timezone_input.setText(self.settings.value("system/default_timezone", "UTC"))
        layout.addWidget(QLabel("Часовой пояс:"))
        layout.addWidget(self.default_timezone_input)

        self.default_locale_input = QLineEdit()
        self.default_locale_input.setPlaceholderText("Введите язык")
        self.default_locale_input.setText(self.settings.value("system/default_locale", "en_US"))
        layout.addWidget(QLabel("Язык:"))
        layout.addWidget(self.default_locale_input)

        tab.setLayout(layout)
        return tab

    def browse_data_path(self):
        """
        Открывает диалог выбора пути к данным.
        """
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку данных")
        if directory:
            self.data_path_input.setText(directory)

    def save_settings(self):
        """
        Сохраняет настройки из всех вкладок в INI-файл.
        """
        try:
            # Сохраняем настройки API
            self.settings.setValue("api/endpoint", self.api_endpoint_input.text())
            self.settings.setValue("api/port", self.api_port_input.text())

            # Сохраняем настройки Данных
            self.settings.setValue("data/path", self.data_path_input.text())

            # Сохраняем настройки Системы
            self.settings.setValue("system/default_timezone", self.default_timezone_input.text())
            self.settings.setValue("system/default_locale", self.default_locale_input.text())

            self.settings.sync()  # Принудительно записываем в файл
            QMessageBox.information(self, "Успех", "Настройки сохранены.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки: {e}")


class Toolbar(QToolBar):
    def __init__(self, token, parent=None):
        super().__init__(parent)
        self.token = token

        self.setMovable(False)  # Фиксируем панель инструментов

        # Добавляем действия на панель
        self.add_actions()

    def add_actions(self):
        """
        Добавляем действия на панель инструментов.
        """
        # Действие "Start Bot"
        start_bot_action = QAction(QIcon("icons/start.png"), "Запустить бота", self)
        start_bot_action.setStatusTip("Запустить Telegram-бота")
        start_bot_action.triggered.connect(self.start_bot)
        self.addAction(start_bot_action)

        # Действие "Stop Bot"
        stop_bot_action = QAction(QIcon("icons/stop.png"), "Остановить бота", self)
        stop_bot_action.setStatusTip("Остановить Telegram-бота")
        stop_bot_action.triggered.connect(self.stop_bot)
        self.addAction(stop_bot_action)

        # Действие "Restart Bot"
        restart_bot_action = QAction(QIcon("icons/restart.png"), "Перезапустить бота", self)
        restart_bot_action.setStatusTip("Перезапустить Telegram-бота")
        restart_bot_action.triggered.connect(self.restart_bot)
        self.addAction(restart_bot_action)
        # Разделитель
        self.addSeparator()

        # Действие "Обновить"
        refresh_action = QAction(QIcon("icons/refresh.png"), "Обновить", self)
        refresh_action.setStatusTip("Обновить данные")
        refresh_action.triggered.connect(self.on_refresh)
        self.addAction(refresh_action)

        # Действие "Настройки"
        settings_action = QAction(QIcon("icons/settings.png"), "Настройки", self)
        settings_action.setStatusTip("Открыть настройки")
        settings_action.triggered.connect(self.on_settings)
        self.addAction(settings_action)

        # Разделитель
        self.addSeparator()

        # Действие "О программе"
        about_action = QAction("О программе", self)
        about_action.setStatusTip("Информация о приложении")
        about_action.triggered.connect(self.on_about)
        self.addAction(about_action)

    def on_refresh(self):
        """
        Обработчик действия "Обновить".
        """
        QMessageBox.information(self, "Обновить", "Данные успешно обновлены!")

    def on_settings(self):
        """
        Обработчик действия "Настройки".
        """
        dialog = SettingsDialog()
        dialog.exec_()
        # QMessageBox.information(self, "Настройки", "Настройки открыты!")

    def on_about(self):
        """
        Обработчик действия "О программе".
        """
        QMessageBox.information(
            self,
            "О программе",
            "Админ-панель TgNSA\nВерсия: 0.1.0\nРазработано с использованием PyQt5.",
        )

    def start_bot(self):
        """
        Отправляет POST-запрос на запуск бота.
        """
        try:
            url = f"{self.api_base_url}/start_bot/"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}

            response = api_request("POST", url, headers=headers)
            response.raise_for_status()
            QMessageBox.information(self, "Успех", "Бот успешно запущен!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить бота:\n{e}")

    def stop_bot(self):
        """
        Отправляет POST-запрос на остановку бота.
        """
        try:
            url = f"{self.api_base_url}/stop_bot/"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}

            response = api_request("POST", url, headers=headers)
            response.raise_for_status()
            QMessageBox.information(self, "Успех", "Бот успешно остановлен!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось остановить бота:\n{e}")

    def restart_bot(self):
        """
        Отправляет POST-запрос на перезапуск бота.
        """
        try:
            url = f"{self.api_base_url}/restart_bot/"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}

            response = api_request("POST", url, headers=headers)

            response.raise_for_status()
            QMessageBox.information(self, "Успех", "Бот успешно перезапущен!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось перезапустить бота:\n{e}")


class UserEditDialog(QDialog):
    def __init__(self, user_data, api_base_url, token, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.api_base_url = api_base_url
        self.token = token
        self.setWindowTitle("Редактирование профиля пользователя")
        self.setGeometry(300, 200, 400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Форма для редактирования данных
        form_layout = QFormLayout()

        self.first_name_input = QLineEdit(self.user_data.get("first_name", ""))
        form_layout.addRow("Имя:", self.first_name_input)

        self.last_name_input = QLineEdit(self.user_data.get("last_name", ""))
        form_layout.addRow("Фамилия:", self.last_name_input)

        self.email_input = QLineEdit(self.user_data.get("email", ""))
        form_layout.addRow("E-mail:", self.email_input)

        self.phone_input = QLineEdit(self.user_data.get("phone_number", ""))
        form_layout.addRow("Телефон:", self.phone_input)

        self.company_post_input = QLineEdit(self.user_data.get("company_post", ""))
        form_layout.addRow("Должность:", self.company_post_input)

        self.station_input = QLineEdit(self.user_data.get("station", ""))
        form_layout.addRow("Станция:", self.station_input)

        self.is_admin_checkbox = QCheckBox()
        self.is_admin_checkbox.setChecked(self.user_data.get("is_admin", False))
        form_layout.addRow("Администратор:", self.is_admin_checkbox)

        self.user_allowed_checkbox = QCheckBox()
        self.user_allowed_checkbox.setChecked(self.user_data.get("user_allowed", True))
        form_layout.addRow("Разрешён:", self.user_allowed_checkbox)

        self.user_verified_checkbox = QCheckBox()
        self.user_verified_checkbox.setChecked(self.user_data.get("user_verified", True))
        form_layout.addRow("Верифицирован:", self.user_verified_checkbox)

        layout.addLayout(form_layout)

        # Кнопки "Сохранить" и "Отмена"
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_user_data)
        layout.addWidget(save_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

    def save_user_data(self):
        updated_data = {
            "first_name": self.first_name_input.text(),
            "last_name": self.last_name_input.text(),
            "email": self.email_input.text(),
            "phone_number": self.phone_input.text(),
            "company_post": self.company_post_input.text(),
            "station": self.station_input.text(),
            "is_admin": self.is_admin_checkbox.isChecked(),
            "user_allowed": self.user_allowed_checkbox.isChecked(),
            "user_verified": self.user_verified_checkbox.isChecked(),
        }

        try:
            url = f"{self.api_base_url}/user/{self.user_data['tg_id']}"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
            response = api_request("PUT", url, headers=headers, json_data=updated_data)
            response.raise_for_status()
            QMessageBox.information(self, "Успех", "Данные пользователя успешно обновлены.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить данные пользователя:\n{e}")


class UsersTab(BaseTab):
    def __init__(self, api_base_url: str, token: str, parent=None):
        super().__init__(api_base_url, token, parent)  # Передача аргументов в базовый класс
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.user_table = QTableWidget()
        self.user_table.setColumnCount(7)
        self.user_table.setHorizontalHeaderLabels(
            ["ID", "Имя", "Фамилия", "Должность", "Телефон", "E-mail", "Действия"])
        self.user_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Запрет редактирования ячеек
        self.user_table.setSortingEnabled(True)
        layout.addWidget(self.user_table)

        refresh_button = QPushButton("Обновить список пользователей")
        refresh_button.clicked.connect(self.load_users)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

    def handle_exception(self, action: str, exception: Exception):
        QMessageBox.critical(self, "Ошибка", f"Не удалось {action}:\n{exception}")

    def load_users(self):

        try:
            url = f"{self.api_base_url}/users/"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
            response = api_request("GET", url, headers=headers)
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError(f"Ошибка сервера: {response.status_code} {response.reason_phrase}")
            users = response.json()
            self.populate_user_table(users)
        except Exception as e:
            self.handle_exception("загрузить пользователей", e)

    def populate_user_table(self, users):
        """
        Заполняет таблицу пользователей на основе предоставленных данных.
        """
        try:
            self.user_table.setRowCount(0)  # Очистка таблицы

            for user in users:
                try:
                    # Добавляем новую строку
                    row_position = self.user_table.rowCount()
                    self.user_table.insertRow(row_position)

                    # Заполняем ячейки строки
                    self.user_table.setItem(row_position, 0, self.create_aligned_item(str(user.get("tg_id", ""))))
                    self.user_table.setItem(row_position, 1, self.create_aligned_item(user.get("first_name", "")))
                    self.user_table.setItem(row_position, 2, self.create_aligned_item(user.get("last_name", "")))
                    self.user_table.setItem(row_position, 3, self.create_aligned_item(user.get("company_post", "")))
                    self.user_table.setItem(row_position, 4, self.create_aligned_item(user.get("phone_number", "")))
                    self.user_table.setItem(row_position, 5, self.create_aligned_item(user.get("email", "")))

                    # Добавляем кнопку удаления
                    delete_button = QPushButton("Удалить")
                    delete_button.setStyleSheet("background-color: red; color: white;")
                    delete_button.clicked.connect(lambda _, user_id=user.get("tg_id"): self.delete_user(user_id))
                    self.user_table.setCellWidget(row_position, 6, delete_button)

                except Exception as row_error:
                    continue

            # Применяем автоматическую подгонку ширины столбцов
            self.user_table.resizeColumnsToContents()
            self.user_table.cellDoubleClicked.connect(self.handle_user_double_click)
            # Настраиваем высоту строк
            self.user_table.verticalHeader().setDefaultSectionSize(40)

            # Настраиваем заголовки
            header = self.user_table.horizontalHeader()
            header.setStyleSheet("font-weight: bold; background-color: #f0f0f0;")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось заполнить таблицу пользователей:\n{e}")

    def create_aligned_item(self, text):
        """
        Создает элемент таблицы с выравниванием текста по центру.
        """
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def handle_user_double_click(self, row, column):
        """
        Обрабатывает двойной клик по строке таблицы.
        """
        try:
            user_id_item = self.user_table.item(row, 0)
            if user_id_item:
                user_id = user_id_item.text()
                self.show_user_profile(user_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть профиль пользователя:\n{e}")

    def show_user_profile(self, user_id):
        """
        Показывает профиль пользователя по его идентификатору.
        """
        try:
            url = f"{self.api_base_url}/user/{user_id}"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
            response = api_request("GET", url, headers=headers)
            response.raise_for_status()
            user_data = response.json()

            dialog = UserEditDialog(user_data, self.api_base_url, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_users()  # Перезагрузка таблицы после изменения
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить профиль пользователя:\n{e}")

    def delete_user(self, user_id):
        try:
            url = f"{self.api_base_url}/user/{user_id}"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
            response = api_request("DELETE", url, headers=headers)
            response.raise_for_status()
            QMessageBox.information(self, "Успех", f"Пользователь с ID {user_id} удалён.")
            self.load_users()
        except Exception as e:
            self.handle_exception("удалить пользователя", e)


class MessagesTab(BaseTab):
    def __init__(self, api_base_url: str, token: str, parent=None):
        super().__init__(api_base_url, token, parent)  # Передача аргументов в базовый класс
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Поле для ID пользователя
        user_id_layout = QHBoxLayout()
        user_id_label = QLabel("ID пользователя:")
        self.message_user_id = QLineEdit()
        user_id_layout.addWidget(user_id_label)
        user_id_layout.addWidget(self.message_user_id)
        layout.addLayout(user_id_layout)

        # Поле для текста сообщения
        message_layout = QHBoxLayout()
        message_label = QLabel("Текст сообщения:")
        self.message_text = QLineEdit()
        message_layout.addWidget(message_label)
        message_layout.addWidget(self.message_text)
        layout.addLayout(message_layout)

        # Добавление кнопок
        button_layout = QHBoxLayout()
        send_button = QPushButton("Отправить сообщение")
        send_button.clicked.connect(self.send_message)
        button_layout.addWidget(send_button)

        broadcast_button = QPushButton("Отправить всем")
        broadcast_button.clicked.connect(self.broadcast_message)
        button_layout.addWidget(broadcast_button)

        layout.addLayout(button_layout)

        # Добавление растягивающего пространства для лучшего размещения
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)

    def send_message(self):
        user_id = self.message_user_id.text()
        message = self.message_text.text()
        if not user_id or not message:
            QMessageBox.warning(self, "Ошибка", "ID пользователя и текст сообщения не могут быть пустыми.")
            return
        try:
            response = httpx.post(f"{self.api_base_url}/send_message/", json={"user_id": user_id, "message": message},
                                  headers={"Authorization": f"Bearer {self.token}"}
                                  )
            response.raise_for_status()
            QMessageBox.information(self, "Успех", "Сообщение отправлено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить сообщение:\n{e}")

    def broadcast_message(self):
        message = self.message_text.text()
        if not message:
            QMessageBox.warning(self, "Ошибка", "Текст сообщения не может быть пустым.")
            return
        try:
            response = httpx.post(f"{self.api_base_url}/broadcast/", json={"message": message},
                                  headers={"Authorization": f"Bearer {self.token}"}
                                  )
            response.raise_for_status()
            QMessageBox.information(self, "Успех", "Сообщение отправлено всем пользователям.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить сообщение:\n{e}")


class ConfigTab(BaseTab):
    def __init__(self, api_base_url: str, token: str, parent=None):
        super().__init__(api_base_url, token, parent)  # Передача аргументов в базовый класс
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Ввод ключа конфигурации
        self.config_key_input = QLineEdit()
        self.config_key_input.setPlaceholderText("Введите ключ конфигурации")
        layout.addWidget(self.config_key_input)

        # Кнопка получения значения
        get_config_button = QPushButton("Получить значение")
        get_config_button.clicked.connect(self.get_config_value)
        layout.addWidget(get_config_button)

        # Отображение значения конфигурации
        self.config_value_label = QLabel("Значение: ")
        layout.addWidget(self.config_value_label)

        button_layout = QHBoxLayout()

        # Кнопка обновления конфигурации
        update_button = QPushButton("Обновить конфигурацию")
        update_button.clicked.connect(self.update_config)
        button_layout.addWidget(update_button)

        # Кнопка экспорта конфигурации
        export_button = QPushButton("Экспорт конфигурации")
        export_button.clicked.connect(self.export_config)
        button_layout.addWidget(export_button)

        # Кнопка импорта конфигурации
        import_button = QPushButton("Импорт конфигурации")
        import_button.clicked.connect(self.import_config)
        button_layout.addWidget(import_button)

        layout.addLayout(button_layout)

        # Древовидное представление для отображения конфигурации
        self.config_tree = QTreeWidget()
        self.config_tree.setHeaderLabels(["Ключ", "Значение"])
        self.config_tree.itemDoubleClicked.connect(self.edit_tree_item)  # Обработка двойного клика
        layout.addWidget(self.config_tree)

        # Кнопка загрузки всех конфигураций
        load_all_button = QPushButton("Загрузить всю конфигурацию")
        load_all_button.clicked.connect(self.load_all_configs)
        layout.addWidget(load_all_button)

        self.setLayout(layout)

    def get_config_value(self):
        key = self.config_key_input.text()
        if not key:
            QMessageBox.warning(self, "Ошибка", "Ключ конфигурации не может быть пустым.")
            return
        try:
            response = httpx.get(f"{self.api_base_url}/config/{key}", headers={"Authorization": f"Bearer {self.token}"}
                                 )
            response.raise_for_status()
            value = response.json().get(key, "Не найдено")
            self.config_value_label.setText(f"Значение: {value}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить значение конфигурации:\n{e}")

    def update_config(self):
        QMessageBox.information(self, "Информация", "Функционал обновления конфигурации пока не реализован.")

    def export_config(self):
        try:
            response = httpx.post(f"{self.api_base_url}/config/export",
                                  headers={"Authorization": f"Bearer {self.token}"}
                                  )
            response.raise_for_status()
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить конфигурацию", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, "w") as f:
                    json.dump(response.json(), f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "Успех", "Конфигурация экспортирована.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать конфигурацию:\n{e}")

    def import_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл конфигурации", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, "r") as f:
                config_data = json.load(f)
            response = httpx.post(f"{self.api_base_url}/config/import", json=config_data,
                                  headers={"Authorization": f"Bearer {self.token}"}
                                  )
            response.raise_for_status()
            QMessageBox.information(self, "Успех", "Конфигурация импортирована.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать конфигурацию:\n{e}")

    def load_all_configs(self):
        try:
            response = httpx.get(f"{self.api_base_url}/config/", headers={"Authorization": f"Bearer {self.token}"}
                                 )
            response.raise_for_status()
            config_data = response.json()
            self.populate_config_tree(config_data)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить конфигурации:\n{e}")

    def populate_config_tree(self, config_data):
        """
        Заполняет древовидное представление конфигурацией.
        """
        self.config_tree.clear()
        self.add_items_to_tree(self.config_tree.invisibleRootItem(), config_data)

    def add_items_to_tree(self, parent_item, data):
        """
        Рекурсивно добавляет элементы в дерево.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem([key, str(value) if not isinstance(value, (dict, list)) else ""])
                parent_item.addChild(item)
                self.add_items_to_tree(item, value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem([f"[{index}]", str(value) if not isinstance(value, (dict, list)) else ""])
                parent_item.addChild(item)
                self.add_items_to_tree(item, value)
        else:
            parent_item.setText(1, str(data))

    def edit_tree_item(self, item, column):
        """
        Открывает диалог для редактирования значения элемента.
        """
        if column == 1:  # Разрешаем редактировать только значения
            value, ok = QInputDialog.getText(self, "Редактировать значение", "Новое значение:", text=item.text(1))
            if ok and value:
                item.setText(1, value)
                self.update_config_value_in_api(item)

    def update_config_value_in_api(self, item):
        """
        Обновляет значение конфигурации в API.
        """
        key = item.text(0)
        value = item.text(1)
        try:
            response = httpx.post(f"{self.api_base_url}/config/", json={key: value},
                                  headers={"Authorization": f"Bearer {self.token}"}
                                  )
            response.raise_for_status()
            QMessageBox.information(self, "Успех", f"Значение для '{key}' обновлено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить значение конфигурации:\n{e}")


class MonitoringTab(BaseTab):
    def __init__(self, api_base_url: str, token: str, parent=None):
        super().__init__(api_base_url, token, parent)  # Передача аргументов в базовый класс
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Кнопка для обновления статуса системы
        self.refresh_button = QPushButton("Обновить статус системы")
        self.refresh_button.clicked.connect(self.check_health_status)
        layout.addWidget(self.refresh_button)

        # Таблица для отображения статусов
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels(["Сервис", "Статус", "Детали", "Последняя проверка (сек)"])
        layout.addWidget(self.status_table)

        # Информация о статусе в заголовке
        self.overall_status_label = QLabel("Общий статус: Неизвестно")
        layout.addWidget(self.overall_status_label)

        self.setLayout(layout)

    def check_health_status(self):
        try:
            # Отправляем запрос к API
            response = httpx.get(f"{self.api_base_url}/health/status", headers={"Authorization": f"Bearer {self.token}"}
                                 , timeout=10)
            response.raise_for_status()
            health_data = response.json()

            # Обновляем таблицу с данными
            self.populate_status_table(health_data)

            # Устанавливаем общий статус
            overall_status = "OK" if all(service["status"] == "OK" for service in health_data.values()) else "FAILED"
            self.overall_status_label.setText(f"Общий статус: {overall_status}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось проверить статус системы:\n{e}")

    def populate_status_table(self, health_data):
        # Очищаем таблицу
        self.status_table.setRowCount(0)

        for service_name, service_data in health_data.items():
            row_position = self.status_table.rowCount()
            self.status_table.insertRow(row_position)

            # Заполняем строки таблицы
            self.status_table.setItem(row_position, 0, QTableWidgetItem(service_data.get("title", service_name)))
            self.status_table.setItem(row_position, 1, QTableWidgetItem(service_data.get("status", "Неизвестно")))
            self.status_table.setItem(row_position, 2, QTableWidgetItem(service_data.get("details", "Нет данных")))
            self.status_table.setItem(row_position, 3, QTableWidgetItem(str(service_data.get("last_checked", "N/A"))))

        self.status_table.resizeColumnsToContents()


class MainWindow(QMainWindow):
    def __init__(self, server_endpoint, server_port, token: str = None):
        try:
            super().__init__()
            self.api_base_url = f"http://{server_endpoint}:{server_port}/api"
            self.token = token
            print(token)
            self.setWindowTitle("Админ-панель TgNSA")
            self.setGeometry(100, 100, 1200, 850)

            # Добавляем Toolbar
            self.toolbar = Toolbar(self)
            self.addToolBar(self.toolbar)

            # Центральный виджет
            self.central_widget = QWidget(self)
            self.setCentralWidget(self.central_widget)

            # Вкладки
            self.tabs = QTabWidget(self.central_widget)
            self.tabs.setGeometry(0, 0, 1200, 800)  # Устанавливаем размер для вкладок
            # Здесь можно добавлять вкладки, например:
            self.tabs.addTab(UsersTab(self.api_base_url, token=self.token), "Пользователи")
            self.tabs.addTab(MessagesTab(self.api_base_url, token=self.token), "Сообщения")
            self.tabs.addTab(ConfigTab(self.api_base_url, token=self.token), "Конфигурация")
            self.tabs.addTab(MonitoringTab(self.api_base_url, token=self.token), "Мониторинг")

        except Exception as e:
            QMessageBox.critical(
                None, "Ошибка", f"Ошибка при инициализации главного окна:\n{e}"
            )
            raise
