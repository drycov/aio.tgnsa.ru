import sys
from datetime import timezone

import httpx
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from jose import jwt, ExpiredSignatureError, JWTError

from adminGUI.forms import MainWindow
from adminGUI.forms.Main import SettingsDialog, LoginDialog


def load_settings():
    """
    Загружает настройки из config.ini и возвращает endpoint и port.
    """
    settings = QSettings("config.ini", QSettings.IniFormat)
    endpoint = settings.value("api/endpoint", "")
    port = settings.value("api/port", "")
    return endpoint, port


def save_settings(endpoint, port):
    """
    Сохраняет настройки в config.ini.
    """
    settings = QSettings("config.ini", QSettings.IniFormat)
    settings.setValue("api/endpoint", endpoint)
    settings.setValue("api/port", port)
    settings.sync()


def validate_api_connection(endpoint, port):
    """
    Проверяет доступность API.
    """
    try:
        url = f"http://{endpoint}:{port}/api/ping"
        response = httpx.get(url, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Ошибка соединения с API: {e}")
        return False


def is_token_valid(token):
    """
    Проверяет срок действия токена.
    :param token: JWT-токен в строковом формате.
    :return: True, если токен действителен; False, если токен истёк.
    """
    try:
        # Декодируем токен без проверки подписи
        payload = jwt.decode(token, key=None, options={"verify_signature": False})
        exp = payload.get("exp")
        if not exp:
            print("Поле 'exp' отсутствует в токене.")
            return False

        # Проверяем время истечения
        from datetime import datetime
        now = datetime.now(timezone.utc).timestamp()

        if now > exp:
            print("Токен истёк.")
            return False

        return True
    except ExpiredSignatureError:
        print("Токен истёк.")
        return False
    except JWTError as e:
        print(f"Ошибка JWT: {e}")
        return False


def configure_api():
    """
    Открывает диалог настроек для задания параметров API.
    """
    settings_dialog = SettingsDialog()
    if settings_dialog.exec_() == QDialog.Accepted:
        return load_settings()
    else:
        return None, None, None


def main():
    app = QApplication(sys.argv)

    try:
        # Загрузка настроек
        endpoint, port = load_settings()

        # Если настройки отсутствуют, открываем диалог настроек
        if not endpoint or not port:
            QMessageBox.information(None, "Настройки", "Настройки не найдены. Укажите параметры API.")
            endpoint, port = configure_api()

            if not endpoint or not port:
                print("Настройки не заданы. Завершение программы.")
                sys.exit(0)

        # Проверяем соединение с API
        while not validate_api_connection(endpoint, port):
            QMessageBox.warning(None, "Ошибка соединения", "Не удалось подключиться к API. Проверьте настройки.")
            endpoint, port, token = configure_api()

            if not endpoint or not port:
                print("Соединение с API не установлено. Завершение программы.")
                sys.exit(0)

        print(f"Загрузка приложения с настройками: endpoint={endpoint}, port={port}")

        # Проверяем токен авторизации
        settings = QSettings("config.ini", QSettings.IniFormat)
        token = settings.value("auth/token", "")

        if not token or not is_token_valid(token):
            # Если токен отсутствует или истёк, запросим авторизацию
            login_dialog = LoginDialog(api_base_url=f"http://{endpoint}:{port}")
            if login_dialog.exec_() != QDialog.Accepted:
                print("Авторизация не выполнена. Завершение программы.")
                sys.exit(0)

        # Инициализация основного окна
        main_window = MainWindow(server_endpoint=endpoint, server_port=port, token=token)
        main_window.show()
        sys.exit(app.exec_())

    except Exception as e:
        QMessageBox.critical(None, "Критическая ошибка", f"Ошибка при запуске приложения:\n{e}")
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
