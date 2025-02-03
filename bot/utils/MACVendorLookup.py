import requests
import json
import re
from pathlib import Path
from typing import Dict, Optional

from config import Config

class MACVendorLookup:
    IEEE_URL = "https://standards-oui.ieee.org/oui/oui.txt"  # URL для загрузки OUI/MA-L данных
    MAC_TO_COMPANY_RE = re.compile(r"([0-9A-F-]+)\s+\(hex\)\s+(.+?)\n", re.VERBOSE)


    def __init__(self, data_file: Path = Path(Config.DATA_PATH) / "latest_oui_lookup.json"):
        self.data_file = data_file
        self.macs_to_companies: Dict[str, Dict[str, str]] = {}

    def download_ieee_data(self) -> Optional[str]:
        """Download MAC OUI data from IEEE site."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(self.IEEE_URL, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error downloading data: {e}")
            return None

    def parse(self, text_str: str) -> Dict[str, Dict[str, str]]:
        """Parse text data from IEEE."""
        matches = self.MAC_TO_COMPANY_RE.findall(text_str)
        if matches:
            parsed_data = {}
            for match in matches:
                mac_hex = match[0].replace("-", "")  # Убираем дефисы из MAC-адреса
                organization = match[1].strip() if match[1] else "No address" # Название компании
                parsed_data[mac_hex] = {
                    "organization": organization,
                }
            return parsed_data
        else:
            print("No match found.")
            return {}

    def update_data(self) -> bool:
        """Download, parse, and store the IEEE OUI data."""
        ieee_data = self.download_ieee_data()
        if ieee_data:
            parsed_data = self.parse(ieee_data)
            # Сортировка по организации
            self.macs_to_companies = dict(sorted(parsed_data.items(), key=lambda item: item[1]["organization"]))
            return True
        return False

    def save_to_file(self) -> None:
        """Save the parsed data to a JSON file."""
        try:
            self.data_file.write_text(
                json.dumps(self.macs_to_companies, indent=4, ensure_ascii=False),
                encoding="utf-8"
            )
            print(f"Data successfully saved to {self.data_file}")
        except Exception as e:
            print(f"Error saving data to file: {e}")

    def load_from_file(self) -> None:
        """Load previously saved data from a JSON file."""
        if self.data_file.exists():
            try:
                with self.data_file.open(encoding="utf-8") as file:
                    self.macs_to_companies = json.load(file)
            except Exception as e:
                print(f"Error loading data from file: {e}")
        else:
            print(f"File {self.data_file} does not exist.")

    def get_manufacturer(self, mac_address: str) -> str:
        """Return manufacturer name for a single MAC address or list of MAC addresses."""
        # Преобразуем MAC-адрес в стандартный формат (первые 6 символов)
        def format_mac(mac: str) -> str:
            return mac.upper().replace(":", "").replace("-", "")[:6]

        if isinstance(mac_address, list):
            manufacturers = []
            for address in mac_address:
                mac_prefix = format_mac(address)
                manufacturer = self.macs_to_companies.get(mac_prefix)
                manufacturers.append(manufacturer["organization"] if manufacturer else "Manufacturer not found")
            return manufacturers
        else:
            mac_prefix = format_mac(mac_address)
            manufacturer = self.macs_to_companies.get(mac_prefix)
            return manufacturer["organization"] if manufacturer else "Manufacturer not found"


if __name__ == "__main__":
    mac_lookup = MACVendorLookup()

    # Загружаем сохраненные данные, если они есть
    mac_lookup.load_from_file()

    # Обновляем данные, если они не загружены
    if not mac_lookup.macs_to_companies:
        if mac_lookup.update_data():
            mac_lookup.save_to_file()

    # Пример использования: Получение производителя по MAC-адресу
    mac_address = "00:14:22:01:23:45"
    manufacturer = mac_lookup.get_manufacturer(mac_address)

    if manufacturer:
        print(f"Manufacturer for MAC {mac_address}: {manufacturer}")
    else:
        print(f"Manufacturer for MAC {mac_address} not found.")