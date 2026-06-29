"""
friday.memory.working — Task-scoped working memory that lives in RAM only.
The snapshot() method writes to vault/debug/ for crash recovery only.
This snapshot is never read back as truth by any other module.
"""

import os
import json
from dataclasses import dataclass, field
from typing import List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNAPSHOT_PATH = os.path.join(PROJECT_ROOT, "vault", "debug", "working_snapshot.json")


@dataclass
class WorkingMemory:
    current_goal: str = ""
    current_plan: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    open_loops: List[str] = field(default_factory=list)
    pending_questions: List[str] = field(default_factory=list)
    temporary_notes: List[str] = field(default_factory=list)

    def clear(self):
        """Reset all fields to empty defaults."""
        self.current_goal = ""
        self.current_plan = []
        self.observations = []
        self.open_loops = []
        self.pending_questions = []
        self.temporary_notes = []

    def snapshot(self):
        """Write current state to vault/debug/working_snapshot.json for crash recovery only.
        This snapshot is never read back as truth by any other module."""
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        data = {
            "current_goal": self.current_goal,
            "current_plan": self.current_plan,
            "observations": self.observations,
            "open_loops": self.open_loops,
            "pending_questions": self.pending_questions,
            "temporary_notes": self.temporary_notes,
        }
        try:
            with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WorkingMemory] Snapshot failed: {e}")
