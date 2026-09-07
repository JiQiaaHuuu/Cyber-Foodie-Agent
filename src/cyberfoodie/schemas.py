from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FoodPreference:
    taste: str = "辣"
    budget: int = 25
    weather: str = "晴"
    avoid: str = "无"
    scene: str = "普通午餐"
    mood: str = "想吃得满足"


@dataclass
class AgentProfile:
    name: str
    tagline: str
    style: str
    color: str


@dataclass
class MenuItem:
    name: str
    source: str
    price: int
    category: str
    tags: List[str]
    weather_fit: List[str]
    available_time: List[str]
    popularity: int
    desc: str


@dataclass
class DebateSpeech:
    round: int
    agent: str
    agent_key: str
    dish_name: str
    dish_source: str
    content: str
    source: str
    time: str


@dataclass
class BattleReport:
    winner_agent: str
    recommended_dish: str
    backup_dish: str
    score: Dict[str, int] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    risk: str = ""
    summary: str = ""
    source: str = "local"
