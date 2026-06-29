"""
friday.identity — Loads and exposes FRIDAY's stable identity from vault/identity.json.
Identity is read-only at runtime. No module may write to it except update_identity().
"""

import os
import json
from dataclasses import dataclass, field
from typing import List

# Resolve vault path relative to project root (one level above friday/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDENTITY_PATH = os.path.join(PROJECT_ROOT, "vault", "identity.json")

DEFAULT_IDENTITY = {
    "mission": "Assist Vatsal as a locally-running intelligent agent with full PC control",
    "values": ["honesty", "efficiency", "privacy", "continuous improvement"],
    "personality": "concise, direct, intelligent, calm",
    "communication_style": "short responses unless detail is needed, no filler phrases",
    "constraints": [
        "never hallucinate file paths",
        "never use placeholder usernames",
        "always use C:\\Users\\LP082W\\ for file paths",
        "never claim inability when a tool exists"
    ]
}


@dataclass(frozen=True)
class Identity:
    mission: str
    values: List[str]
    personality: str
    communication_style: str
    constraints: List[str]


def load_identity() -> Identity:
    """Read vault/identity.json and return an Identity dataclass.
    If the file doesn't exist, create it with sensible defaults."""
    if not os.path.exists(IDENTITY_PATH):
        os.makedirs(os.path.dirname(IDENTITY_PATH), exist_ok=True)
        with open(IDENTITY_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_IDENTITY, f, indent=2)
        data = DEFAULT_IDENTITY
    else:
        with open(IDENTITY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

    return Identity(
        mission=data.get("mission", DEFAULT_IDENTITY["mission"]),
        values=data.get("values", DEFAULT_IDENTITY["values"]),
        personality=data.get("personality", DEFAULT_IDENTITY["personality"]),
        communication_style=data.get("communication_style", DEFAULT_IDENTITY["communication_style"]),
        constraints=data.get("constraints", DEFAULT_IDENTITY["constraints"]),
    )


def update_identity(new_data: dict, confirm: bool = False) -> bool:
    """Update identity.json. Gated behind a confirmation flag.
    Returns True if updated, False if blocked."""
    if not confirm:
        print("[Identity] Update blocked: confirmation flag not set.")
        return False

    if not os.path.exists(IDENTITY_PATH):
        current = DEFAULT_IDENTITY.copy()
    else:
        with open(IDENTITY_PATH, "r", encoding="utf-8") as f:
            current = json.load(f)

    current.update(new_data)
    with open(IDENTITY_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    print("[Identity] Updated successfully.")
    return True
