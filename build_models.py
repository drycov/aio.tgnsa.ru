import json
import re
import toml
import argparse
from pathlib import Path
import requests
from functools import lru_cache


SCORE_BASE = 100


def load_device_data(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=128)
def query_model_info(model_key: str, enable_lookup: bool = False) -> dict:
    if not enable_lookup:
        return {"description": "", "brand": ""}

    # Пример заготовки под lookup (реализуемый через внешние API)
    try:
        resp = requests.get(f"https://en.wikipedia.org/w/api.php", params={
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": model_key
        }, timeout=5)
        data = resp.json()
        if data["query"]["search"]:
            title = data["query"]["search"][0]["title"]
            return {
                "description": title,
                "brand": model_key.split()[0] if " " in model_key else ""
            }
    except Exception:
        pass
    return {"description": "", "brand": ""}


def infer_rule(key: str, attrs: dict, enable_lookup: bool = False) -> dict:
    info = query_model_info(key, enable_lookup)
    score = SCORE_BASE + attrs.get("fibers", 0)
    rule = {
        "name": attrs.get("name", key),
        "score": score,
        "description": info.get("description", ""),
        "brand": info.get("brand", ""),
    }
    if re.search(r"[^\w\-./]", key) or " " in key:
        rule["match_regex"] = key
    else:
        rule["match"] = key
    return rule


def build_rules(device_data: dict, enable_lookup: bool = False):
    rules = []
    for key, attrs in device_data.items():
        rule = infer_rule(key, attrs, enable_lookup)
        toml_obj = {
            "name": rule["name"],
            "score": rule["score"],
        }
        if "match" in rule:
            toml_obj["match"] = rule["match"]
        elif "match_regex" in rule:
            toml_obj["match_regex"] = rule["match_regex"]
        if rule.get("brand"):
            toml_obj["brand"] = rule["brand"]
        if rule.get("description"):
            toml_obj["description"] = rule["description"]
        rules.append(toml_obj)
    return rules


def write_toml(rules: list, out: Path):
    with out.open("w", encoding="utf-8") as f:
        toml.dump({"models": rules}, f)
    print(f"✅ Models written to: {out}")


def cli():
    parser = argparse.ArgumentParser(
        description="🔧 Convert device JSON into TOML rules for model matching"
    )
    parser.add_argument(
        "-i", "--input", required=True, type=Path, help="Path to input device_data.json"
    )
    parser.add_argument(
        "-o", "--output", default="models.toml", type=Path, help="Output TOML path"
    )
    parser.add_argument(
        "--lookup", action="store_true", help="Enable internet lookup for model metadata"
    )

    args = parser.parse_args()
    data = load_device_data(args.input)
    rules = build_rules(data, enable_lookup=args.lookup)
    write_toml(rules, args.output)


if __name__ == "__main__":
    cli()
