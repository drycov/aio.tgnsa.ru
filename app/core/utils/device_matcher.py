import re
import tomllib
from pathlib import Path
from typing import Literal, Optional
from collections import defaultdict
from pathlib import Path

class ModelRule:
    def __init__(self, name: str, match: str, score: int = 100, kind: Literal["substr", "regex"] = "substr"):
        self.name = name
        self.match = match
        self.score = score
        self.kind = kind

    def matches(self, raw: str) -> bool:
        if self.kind == "substr":
            return self.match in raw
        elif self.kind == "regex":
            return bool(re.search(self.match, raw))
        return False

class ModelMatcher:
    def __init__(self, rules_path: Path):
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, path: Path) -> list[ModelRule]:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        rules = []
        for entry in data.get("models", []):
            if "match" in entry:
                rules.append(ModelRule(entry["name"], entry["match"], entry.get("score", 100), kind="substr"))
            elif "match_regex" in entry:
                rules.append(ModelRule(entry["name"], entry["match_regex"], entry.get("score", 100), kind="regex"))
        return rules

    def match(self, raw: str) -> str:
        best_match = None
        best_score = -1
        for rule in self.rules:
            if rule.matches(raw) and rule.score > best_score:
                best_match = rule.name
                best_score = rule.score
        return best_match or raw  # fallback — вернуть оригинал

def generate_device_model_rules(sysdescr_list: list[str], output_file: Path):
    match_counts = defaultdict(int)

    for descr in sysdescr_list:
        parts = descr.split()
        for part in parts:
            if any(char.isdigit() for char in part) and len(part) > 3:
                match_counts[part] += 1

    # фильтруем по встречаемости
    rules = []
    for match, count in sorted(match_counts.items(), key=lambda x: -x[1]):
        rules.append({
            "name": match,
            "match": match,
            "score": min(100, count * 10),
        })

    with output_file.open("w", encoding="utf-8") as f:
        f.write("[[models]]\n")
        for rule in rules:
            f.write(f'name = "{rule["name"]}"\n')
            f.write(f'match = "{rule["match"]}"\n')
            f.write(f'score = {rule["score"]}\n\n')
