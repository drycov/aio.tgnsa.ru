import requests
import re
from typing import List, Dict

class PENFinder:
    PEN_URL = "https://www.iana.org/assignments/enterprise-numbers.txt"

    @staticmethod
    def fetch_pen_data() -> List[str]:
        """
        Загружает данные Private Enterprise Numbers (PEN) из IANA.

        Returns:
            List[str]: Список строк из файла PEN.
        """
        try:
            response = requests.get(PENFinder.PEN_URL, timeout=10)
            response.raise_for_status()
            return response.text.splitlines()
        except requests.RequestException as e:
            print(f"Ошибка загрузки данных PEN: {e}")
            return []

    @staticmethod
    def search_pen(search_term: str) -> List[Dict[str, str]]:
        """
        Выполняет поиск по Private Enterprise Numbers (PEN).

        Args:
            search_term (str): Строка для поиска (номер PEN, имя организации, контакт или email).

        Returns:
            List[Dict[str, str]]: Результаты поиска (список словарей).
        """
        pen_data = PENFinder.fetch_pen_data()
        if not pen_data:
            return []

        results = []
        current_entry = {"Decimal": None, "Organization": None, "Contact": None, "Email": None}

        pattern = re.compile(r"^(\d+)|^([^@\n]+)|([\w.-]+@[\w.-]+)$")

        for line in pen_data:
            match = pattern.match(line.strip())
            if match:
                if match.group(1):  # Decimal
                    if current_entry["Decimal"] and search_term.lower() in str(current_entry).lower():
                        results.append(current_entry.copy())
                    current_entry = {"Decimal": match.group(1), "Organization": None, "Contact": None, "Email": None}
                elif match.group(2):  # Organization or Contact
                    if not current_entry["Organization"]:
                        current_entry["Organization"] = match.group(2)
                    elif not current_entry["Contact"]:
                        current_entry["Contact"] = match.group(2)
                elif match.group(3):  # Email
                    current_entry["Email"] = match.group(3)

        # Проверка последней записи
        if current_entry["Decimal"] and search_term.lower() in str(current_entry).lower():
            results.append(current_entry)

        return results

    @staticmethod
    def parse_oid(value: str) -> Dict[str, str]:
        """
        Парсит строку OID и возвращает её компоненты.

        Args:
            value (str): Строка OID.

        Returns:
            Dict[str, str]: Словарь с информацией о компонентах OID.
        """
        oid_parts = value.split(".")
        if len(oid_parts) < 7:
            raise ValueError("OID имеет недостаточное количество компонентов.")

        return {
            "iso": oid_parts[0],
            "org": oid_parts[1],
            "dod": oid_parts[2],
            "internet": oid_parts[3],
            "private": oid_parts[4],
            "enterprise": oid_parts[5],
            "pen": oid_parts[6],
            "subtree": ".".join(oid_parts[7:])
        }

# Пример использования:
if __name__ == "__main__":
    # Поиск по PEN
    search_results = PENFinder.search_pen("40418")
    for result in search_results:
        print(result)

    # Парсинг OID
    oid = "1.3.6.1.4.1.40418.7.48"
    parsed_oid = PENFinder.parse_oid(oid)
    print("Распарсенный OID:", parsed_oid)
