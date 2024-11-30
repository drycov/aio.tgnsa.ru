import requests
from urllib3.exceptions import InsecureRequestWarning

# Настройки клиента
SERVER_URL = "https://127.0.0.1:5000"  # Адрес VPN сервера
LOGIN_URL = f"{SERVER_URL}/login"
SECURE_DATA_URL = f"{SERVER_URL}/api/"
USER_ID = "6818244868"
PASSWORD = "password"
VPN_TOKEN = "52ec256a2909145086f6bad46a74a5d5"  # Тестовый токен (замените на актуальный)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def login(userid, password, vpn_token):
    """Отправить запрос на авторизацию."""
    headers = {"X-VPN-Auth": f"Bearer {vpn_token}"}
    payload = {"userid": userid, "password": password}
    try:
        response = requests.post(LOGIN_URL, headers=headers, json=payload, verify=False)
        if response.status_code == 200:
            print(f"Успешный вход. Токен: {response.json()['access_token']}")
            return response.json()["access_token"]
        else:
            print(f"Ошибка входа: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        print(f"Ошибка соединения: {e}")


def get_secure_data(token, vpn_token):
    """Запросить защищённые данные."""
    headers = {"X-VPN-Auth": f"Bearer {vpn_token}",
               "Authorization": f"Bearer {token}"}
    try:
        response = requests.get(SECURE_DATA_URL, headers=headers, verify=False)
        if response.status_code == 200:
            print(f"Получены данные: {response.json()}")
        else:
            print(f"Ошибка доступа: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        print(f"Ошибка соединения: {e}")


if __name__ == "__main__":
    print("\n--- Авторизация ---")
    token = login(USER_ID, PASSWORD, VPN_TOKEN)
    if token:
        print("\n--- Доступ к защищённым данным ---")
        get_secure_data(token, VPN_TOKEN)
