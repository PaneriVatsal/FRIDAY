"""
friday.memory.vault_log — Handles reading and writing to the vault conversation log.
No other module may write to the vault log except this one.
Copied exactly from existing main.py.
"""

import os
import re

VAULT_LOG_PATH = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\memory\current-task.md"

REFUSAL_PHRASES = [
    "i'm sorry", "i cannot", "i don't have permission",
    "as an ai", "i apologize", "i am unable", "i can't",
    "unfortunately", "i do not have the ability",
    "tool_name [", "you can call tools",
    "it seems like the previous response caused an error",
    "let me try again from scratch", "here are some examples of tools"
]


def load_recent_memory(n=20) -> str:
    """Reads VAULT_LOG_PATH and returns last n entries as a string.
    Copied exactly from existing main.py."""
    if not os.path.exists(VAULT_LOG_PATH):
        return ""
    try:
        with open(VAULT_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        parts = re.split(r'\n(?=- \*\*User\*\*:)', content)
        entries = []
        for part in parts:
            part = part.strip()
            if part.startswith("- **User**:"):
                entries.append(part)
            elif "- **User**:" in part:
                subparts = part.split("- **User**:", 1)
                if len(subparts) == 2:
                    entries.append("- **User**:" + subparts[1].strip())

        recent_entries = entries[-n:]
        return "\n\n".join(recent_entries)
    except Exception as e:
        print(f"Error loading recent memory: {e}")
        return ""


def log_to_vault(user_msg: str, model_used: str, final_reply: str):
    """Appends entry to VAULT_LOG_PATH.
    Copied exactly from existing main.py."""
    dir_path = os.path.dirname(VAULT_LOG_PATH)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    indented_reply = "\n".join(f"  {line}" for line in final_reply.splitlines())
    reply_lower = final_reply.lower()
    if any(phrase in reply_lower for phrase in REFUSAL_PHRASES):
        print(f"[Vault] Skipped logging bad response.")
        return
    log_entry = (
        f"- **User**: {user_msg}\n"
        f"- **Model**: `{model_used}`\n"
        f"- **Response**:\n{indented_reply}\n\n"
    )
    try:
        with open(VAULT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error logging to vault: {e}")
