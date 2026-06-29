"""
friday.memory.semantic — Long-term beliefs, confidence-gated.
Reflector may only propose a candidate belief.
promote_to_semantic() only writes if confidence >= 0.75 AND times_reinforced >= 2.
Never written directly by any other module.
"""

import os
import json
import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEMANTIC_PATH = os.path.join(PROJECT_ROOT, "vault", "memory", "semantic.json")


@dataclass
class Belief:
    statement: str
    confidence: float  # 0.0 to 1.0
    times_reinforced: int
    last_updated: str


def _load_store() -> dict:
    """Load the semantic store with 'candidates' and 'promoted' lists."""
    if not os.path.exists(SEMANTIC_PATH):
        return {"candidates": [], "promoted": []}
    try:
        with open(SEMANTIC_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "candidates" not in data:
            data["candidates"] = []
        if "promoted" not in data:
            data["promoted"] = []
        return data
    except (json.JSONDecodeError, Exception):
        return {"candidates": [], "promoted": []}


def _save_store(store: dict):
    """Write the semantic store to disk."""
    os.makedirs(os.path.dirname(SEMANTIC_PATH), exist_ok=True)
    with open(SEMANTIC_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def propose_belief(statement: str, confidence: float):
    """Propose a candidate belief. If it already exists, reinforce it.
    Only the reflector should call this."""
    store = _load_store()
    now = datetime.datetime.now().isoformat()

    # Check if candidate already exists
    for candidate in store["candidates"]:
        if candidate["statement"].lower() == statement.lower():
            candidate["confidence"] = max(candidate["confidence"], confidence)
            candidate["times_reinforced"] += 1
            candidate["last_updated"] = now
            _save_store(store)
            return

    # New candidate
    store["candidates"].append({
        "statement": statement,
        "confidence": confidence,
        "times_reinforced": 1,
        "last_updated": now,
    })
    _save_store(store)


def promote_to_semantic():
    """Apply gating logic: promote candidates with confidence >= 0.75 AND times_reinforced >= 2.
    Moves qualifying candidates to the promoted list."""
    store = _load_store()
    remaining_candidates = []
    for candidate in store["candidates"]:
        if candidate["confidence"] >= 0.75 and candidate["times_reinforced"] >= 2:
            # Check if already promoted (avoid duplicates)
            already_promoted = any(
                p["statement"].lower() == candidate["statement"].lower()
                for p in store["promoted"]
            )
            if not already_promoted:
                store["promoted"].append(candidate)
            else:
                # Update existing promoted belief
                for p in store["promoted"]:
                    if p["statement"].lower() == candidate["statement"].lower():
                        p["confidence"] = max(p["confidence"], candidate["confidence"])
                        p["times_reinforced"] = candidate["times_reinforced"]
                        p["last_updated"] = candidate["last_updated"]
                        break
        else:
            remaining_candidates.append(candidate)
    store["candidates"] = remaining_candidates
    _save_store(store)


def get_beliefs() -> List[Belief]:
    """Return all promoted beliefs."""
    store = _load_store()
    return [
        Belief(
            statement=b.get("statement", ""),
            confidence=b.get("confidence", 0.0),
            times_reinforced=b.get("times_reinforced", 0),
            last_updated=b.get("last_updated", ""),
        )
        for b in store.get("promoted", [])
    ]
