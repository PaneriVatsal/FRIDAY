"""
friday.memory.episodic — Stores past experiences as episodes.
Each episode records a task, tools used, outcome, lesson, and timestamp.
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EPISODIC_PATH = os.path.join(PROJECT_ROOT, "vault", "memory", "episodic.json")


@dataclass
class Episode:
    task: str
    tools_used: List[str]
    outcome: str  # "success" or "failure"
    lesson: str
    timestamp: str


def _load_episodes() -> List[dict]:
    """Load all episodes from disk."""
    if not os.path.exists(EPISODIC_PATH):
        return []
    try:
        with open(EPISODIC_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return []


def _save_episodes(episodes: List[dict]):
    """Write episodes list to disk."""
    os.makedirs(os.path.dirname(EPISODIC_PATH), exist_ok=True)
    with open(EPISODIC_PATH, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2)


def append_episode(episode: Episode):
    """Append an episode to vault/memory/episodic.json."""
    episodes = _load_episodes()
    episodes.append(asdict(episode))
    _save_episodes(episodes)


def get_recent(n: int) -> List[Episode]:
    """Return the last n episodes."""
    episodes = _load_episodes()
    recent = episodes[-n:] if n > 0 else []
    return [
        Episode(
            task=e.get("task", ""),
            tools_used=e.get("tools_used", []),
            outcome=e.get("outcome", ""),
            lesson=e.get("lesson", ""),
            timestamp=e.get("timestamp", ""),
        )
        for e in recent
    ]


def search_episodes(keyword: str) -> List[Episode]:
    """Return episodes matching the keyword in task or lesson."""
    episodes = _load_episodes()
    keyword_lower = keyword.lower()
    matches = []
    for e in episodes:
        task = e.get("task", "").lower()
        lesson = e.get("lesson", "").lower()
        if keyword_lower in task or keyword_lower in lesson:
            matches.append(
                Episode(
                    task=e.get("task", ""),
                    tools_used=e.get("tools_used", []),
                    outcome=e.get("outcome", ""),
                    lesson=e.get("lesson", ""),
                    timestamp=e.get("timestamp", ""),
                )
            )
    return matches
