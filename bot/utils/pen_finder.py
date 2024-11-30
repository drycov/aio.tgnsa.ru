import requests


class PENFinder:
    PEN_URL = "https://www.iana.org/assignments/enterprise-numbers.txt"

    @staticmethod
    def fetch_pen_data() -> list[str]:
        """
        Загружает данные Private Enterprise Numbers (PEN) из IANA.

        Returns:
            list[str]: Список строк из файла PEN.
        """
        try:
            response = requests.get(PENFinder.PEN_URL, timeout=10)
            response.raise_for_status()
            return response.text.splitlines()
        except requests.RequestException as e:
            print(f"Ошибка загрузки данных PEN: {e}")
            return []

    @staticmethod
    def search_pen(search_term: str) -> list[dict]:
        """
        Выполняет поиск по Private Enterprise Numbers (PEN).

        Args:
            search_term (str): Строка для поиска (номер PEN, имя организации, контакт или email).

        Returns:
            list[dict]: Результаты поиска (список словарей).
        """
        pen_data = PENFinder.fetch_pen_data()
        if not pen_data:
            return []

        results = []
        current_entry = {}

        for line in pen_data:
            line = line.strip()

            if line.isdigit():
                # Новая запись
                if current_entry and search_term.lower() in str(current_entry).lower():
                    results.append(current_entry)
                current_entry = {"Decimal": line, "Organization": None, "Contact": None, "Email": None}
            elif "Organization" in current_entry and current_entry["Organization"] is None:
                current_entry["Organization"] = line
            elif "Contact" in current_entry and current_entry["Contact"] is None:
                current_entry["Contact"] = line
            elif "Email" in current_entry and current_entry["Email"] is None:
                current_entry["Email"] = line

        # Проверка последней записи
        if current_entry and search_term.lower() in str(current_entry).lower():
            results.append(current_entry)

        return results

    @staticmethod
    def parse_oid(value: str) -> dict:
        """
        Парсит строку OID и возвращает её компоненты.

        Args:
            value (str): Строка OID.

        Returns:
            dict: Словарь с информацией о компонентах OID.
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
            "subtree": oid_parts[7:]
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
