"""
friday.cognition.planner — Takes the goal and produces an ordered list of steps.
Checks procedural memory for matching strategies first.
If a known strategy exists with success_rate > 0.8, prefer it.
If not, reason from scratch using gemma4:e4b.
Planner never executes. It only plans.
"""

import json
import re
import requests
from friday.memory import procedural

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "gemma4:e4b"


def plan(goal: str, strategy_hint: str = None) -> dict:
    """
    Input: goal, strategy_hint, procedural memory (checked internally)
    Output: {
        "steps": list[str],
        "strategy_used": str or None
    }
    """
    # Check procedural memory first
    best_strategy = procedural.get_best_strategy(goal)
    if best_strategy and best_strategy.success_rate > 0.8:
        print(f"[Planner] Using known strategy: {best_strategy.name} (success_rate={best_strategy.success_rate})")
        return {
            "steps": best_strategy.steps,
            "strategy_used": best_strategy.name,
        }

    # No good strategy found — reason from scratch
    system_prompt = f"""You are FRIDAY's planner. Given a goal, produce an ordered list of concrete steps to accomplish it.

Available tools: run_command, open_app, write_file, read_file, web_search, take_screenshot, fetch_url, get_weather, get_battery_percentage, remember, recall, volume_control, get_volume, type_text, press_hotkey, click_mouse, get_mouse_position, obsidian_write_note, obsidian_read_note, obsidian_search_notes, obsidian_list_notes, get_system_uptime.

Rules:
- Output ONLY valid JSON
- Each step should be a concrete action (e.g., "web_search for current Bitcoin price")
- If no tools are needed (simple conversation), output a single step like "respond directly to user"
- Keep steps minimal and efficient

Output format:
{{
  "steps": ["step 1", "step 2", ...],
  "strategy_used": null
}}
"""

    hint_context = f"\nStrategy hint: {strategy_hint}" if strategy_hint else ""
    strategy_context = ""
    if best_strategy:
        strategy_context = f"\nClosest known strategy: {best_strategy.name} (success_rate={best_strategy.success_rate}, steps={best_strategy.steps})"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Goal: {goal}{hint_context}{strategy_context}"}
    ]

    try:
        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": -1}
        }
        res = requests.post(OLLAMA_URL, json=payload, timeout=60)
        res.raise_for_status()
        content = res.json().get("message", {}).get("content", "").strip()
        print(f"[Planner] Raw response: {content[:300]}")

        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "steps": result.get("steps", [goal]),
                "strategy_used": result.get("strategy_used"),
            }

        # Fallback
        return {"steps": [goal], "strategy_used": None}

    except Exception as e:
        print(f"[Planner] Error: {e}")
        return {"steps": [goal], "strategy_used": None}
