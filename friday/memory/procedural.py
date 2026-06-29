"""
friday.memory.procedural — Stores strategies with performance tracking.
Seeds default strategies on first run.
"""

import os
import json
import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCEDURAL_PATH = os.path.join(PROJECT_ROOT, "vault", "memory", "procedural.json")

DEFAULT_STRATEGIES = [
    {
        "name": "web_search_then_fetch",
        "description": "Search the web for information, then fetch the most relevant URL for detailed content.",
        "steps": ["web_search with query", "fetch_url on best result", "return combined info"],
        "success_rate": 0.91,
        "confidence": 0.9,
        "cost": "medium",
        "when_to_use": "current events, news, real-time information, facts, prices, weather",
        "avoid_when": "user asks a simple conversational question or opinion",
        "failure_modes": ["no search results", "URL fetch timeout", "irrelevant results"],
        "last_used": "",
        "times_used": 0,
    },
    {
        "name": "direct_answer",
        "description": "Answer the user directly without any tool calls.",
        "steps": ["understand the question", "respond with knowledge"],
        "success_rate": 0.98,
        "confidence": 0.95,
        "cost": "low",
        "when_to_use": "simple questions, conversation, greetings, opinions, general knowledge",
        "avoid_when": "user needs real-time data, file operations, or system control",
        "failure_modes": ["outdated knowledge", "missing context"],
        "last_used": "",
        "times_used": 0,
    },
    {
        "name": "open_then_type",
        "description": "Open an application and type text into it.",
        "steps": ["open_app with app name", "wait for app to open", "type_text with content"],
        "success_rate": 0.85,
        "confidence": 0.8,
        "cost": "medium",
        "when_to_use": "user asks to write in an app, type something, open and enter text",
        "avoid_when": "user just wants to open an app without typing",
        "failure_modes": ["app not found", "typing too fast", "wrong window focused"],
        "last_used": "",
        "times_used": 0,
    },
]


@dataclass
class Strategy:
    name: str
    description: str
    steps: List[str]
    success_rate: float
    confidence: float
    cost: str  # "low", "medium", "high"
    when_to_use: str
    avoid_when: str
    failure_modes: List[str]
    last_used: str
    times_used: int


def _load_strategies() -> List[dict]:
    """Load strategies from disk. Seed defaults on first run."""
    if not os.path.exists(PROCEDURAL_PATH):
        os.makedirs(os.path.dirname(PROCEDURAL_PATH), exist_ok=True)
        with open(PROCEDURAL_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_STRATEGIES, f, indent=2)
        return DEFAULT_STRATEGIES.copy()
    try:
        with open(PROCEDURAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return DEFAULT_STRATEGIES.copy()


def _save_strategies(strategies: List[dict]):
    """Write strategies to disk."""
    os.makedirs(os.path.dirname(PROCEDURAL_PATH), exist_ok=True)
    with open(PROCEDURAL_PATH, "w", encoding="utf-8") as f:
        json.dump(strategies, f, indent=2)


def _dict_to_strategy(d: dict) -> Strategy:
    return Strategy(
        name=d.get("name", ""),
        description=d.get("description", ""),
        steps=d.get("steps", []),
        success_rate=d.get("success_rate", 0.0),
        confidence=d.get("confidence", 0.0),
        cost=d.get("cost", "medium"),
        when_to_use=d.get("when_to_use", ""),
        avoid_when=d.get("avoid_when", ""),
        failure_modes=d.get("failure_modes", []),
        last_used=d.get("last_used", ""),
        times_used=d.get("times_used", 0),
    )


def get_best_strategy(goal: str) -> Optional[Strategy]:
    """Return the most relevant strategy by keyword match + success rate."""
    strategies = _load_strategies()
    goal_lower = goal.lower()
    scored = []
    for s in strategies:
        when_keywords = s.get("when_to_use", "").lower().split(", ")
        avoid_keywords = s.get("avoid_when", "").lower()
        # Skip if goal matches avoid_when
        if any(kw in goal_lower for kw in avoid_keywords.split(", ") if kw):
            continue
        # Score by keyword match count + success rate
        match_count = sum(1 for kw in when_keywords if kw and kw in goal_lower)
        if match_count > 0:
            score = match_count * 0.5 + s.get("success_rate", 0.0)
            scored.append((score, s))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return _dict_to_strategy(scored[0][1])


def update_strategy(name: str, success: bool):
    """Update success_rate and confidence for a named strategy."""
    strategies = _load_strategies()
    for s in strategies:
        if s["name"] == name:
            times = s.get("times_used", 0) + 1
            old_rate = s.get("success_rate", 0.5)
            # Exponential moving average
            new_rate = old_rate * 0.8 + (1.0 if success else 0.0) * 0.2
            s["success_rate"] = round(new_rate, 4)
            s["confidence"] = round(min(1.0, s.get("confidence", 0.5) + (0.02 if success else -0.05)), 4)
            s["times_used"] = times
            s["last_used"] = datetime.datetime.now().isoformat()
            _save_strategies(strategies)
            return
    print(f"[Procedural] Strategy '{name}' not found.")


def add_strategy(strategy: Strategy):
    """Add a new strategy to procedural memory."""
    strategies = _load_strategies()
    # Don't add duplicates
    if any(s["name"] == strategy.name for s in strategies):
        print(f"[Procedural] Strategy '{strategy.name}' already exists.")
        return
    strategies.append(asdict(strategy))
    _save_strategies(strategies)


def list_strategies() -> List[Strategy]:
    """Return all strategies."""
    strategies = _load_strategies()
    return [_dict_to_strategy(s) for s in strategies]
