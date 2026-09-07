from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .config import DATA_DIR


def load_menu(menu_file: Path | None = None) -> List[Dict[str, Any]]:
    path = menu_file or DATA_DIR / "real_menu.json"
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_words(value: str) -> List[str]:
    return [word.strip() for word in re.split(r"[，,、\s]+", value or "") if word.strip()]


def score_dish(dish: Dict[str, Any], prefs: Dict[str, Any]) -> int:
    score = 0
    taste = prefs.get("taste", "")
    weather = prefs.get("weather", "")
    budget = int(prefs.get("budget") or 25)
    avoid_words = normalize_words(prefs.get("avoid", ""))
    tags = dish.get("tags", [])

    if dish["price"] <= budget:
        score += 24
    else:
        score -= min(22, dish["price"] - budget)

    if taste and taste in tags:
        score += 30
    if weather and weather in dish.get("weather_fit", []):
        score += 20
    if prefs.get("scene") in dish.get("available_time", []):
        score += 8
    if any(word in dish["name"] or word in "".join(tags) for word in avoid_words if word != "无"):
        score -= 55

    score += int(dish.get("popularity", 0))
    return score


def choose_candidates(menu: List[Dict[str, Any]], prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked = sorted(menu, key=lambda item: score_dish(item, prefs), reverse=True)
    return ranked[:10]
