from typing import Dict, List, Tuple

# 📌 Основная структура
# dept_code -> { "label": str, "positions": [(title, code), ...] }
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

# 📌 Быстрый поиск должности по коду
# code -> (title, dept_code, dept_label)
POSITIONS_BY_CODE: Dict[str, Tuple[str, str, str]] = {}

for dept_code, dept_info in POSITIONS_BY_DEPARTMENT.items():
    dept_label = dept_info["label"]
    for title, code in dept_info["positions"]:
        POSITIONS_BY_CODE[code] = (title, dept_code, dept_label)
