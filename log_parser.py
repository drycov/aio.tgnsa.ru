import re
import pandas as pd
import requests
import click

@click.command()
@click.option('--log_data', prompt='Введите лог данные', help='Лог данных для парсинга')
def process_log(log_data):
    # Регулярное выражение для парсинга
    pattern = re.compile(r"(\d+)\s+(\w+\s+\d+\s+\d+:\d+:\d+\s+\d+)\s+Port security violation \(Port:\s+(\d+),\s+Vid:\s+(\d+),\s+MAC:\s+([\w-]+)\)\s+(\w+)")

    # Извлечение данных из логов
    entries = []
    for match in pattern.finditer(log_data):
        entries.append({
            "Entry": match.group(1),
            "Date": match.group(2),
            "Port": match.group(3),
            "VLAN ID": match.group(4),
            "MAC Address": match.group(5),
            "Warning": match.group(6),
        })

    # Создание DataFrame для удобного просмотра
    df = pd.DataFrame(entries)

    # Функция для получения производителя по MAC-адресу
    def get_mac_vendor(mac):
        response = requests.get(f"https://api.macvendors.com/{mac}")
        if response.status_code == 200:
            return response.text
        else:
            return "Производитель не найден"

    # Добавление столбца с производителем
    df['Vendor'] = df['MAC Address'].apply(get_mac_vendor)

    # Вывод результата
    print(df)

if __name__ == '__main__':
    process_log()
