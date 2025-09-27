# app/bot/constants/positions.py

from typing import Dict, List, Tuple

# Универсальная структура:
# { "КОД_ДЕПАРТАМЕНТА": { "label": "Название департамента", "positions": [(название, код), ...] } }

POSITIONS_BY_DEPARTMENT: Dict[str, Dict[str, List[Tuple[str, str]]]] = {
    "SIT": {
        "label": "СИТ",
        "positions": [
            ("Инженер сети", "sit_engineer"),
            ("Ведущий инженер сети", "sit_lead_engineer"),
        ],
    },
    "TUMS": {
        "label": "ТУМС",
        "positions": [
            ("Механик ТУМС", "tums_mechanic"),
            ("Начальник ТУМС", "tums_chief"),
        ],
    },
    "GOVS": {
        "label": "ГОВС",
        "positions": [
            ("Электромеханник ГОВС", "govs_mechanic"),
            ("Старший электромеханник ГОВС", "govs_senior_mechanic"),
        ],
    },
}
