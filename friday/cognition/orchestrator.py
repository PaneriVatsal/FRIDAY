"""
friday.cognition.orchestrator — Uses gemma4:e4b to understand the user's goal.
It does NOT decide respond/delegate. It only produces a goal.
Uses thinking mode by prepending <|think|> to the system prompt.
"""

import json
import re
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "gemma4:e4b"


def orchestrate(message: str, identity, working_memory, recent_memory: str) -> dict:
    """
    Input: message, identity, working_memory, recent_memory
    Output: {
        "goal": str,
        "strategy_hint": str or None,
        "needs_clarification": bool,
        "clarification_question": str or None
    }
    """
    identity_context = (
        f"Mission: {identity.mission}\n"
        f"Personality: {identity.personality}\n"
        f"Style: {identity.communication_style}\n"
        f"Constraints: {', '.join(identity.constraints)}"
    )

    system_prompt = f"""<|think|>You are FRIDAY's orchestrator. Your ONLY job is to understand the user's goal and produce structured output.

You have access to these tools: run_command, open_app, write_file, read_file, web_search, take_screenshot, fetch_url, get_weather, get_battery_percentage, remember, recall, volume_control, get_volume, type_text, press_hotkey, click_mouse, get_mouse_position, obsidian_write_note, obsidian_read_note, obsidian_search_notes, obsidian_list_notes, get_system_uptime.

Identity:
{identity_context}

Working Memory:
- Current goal: {working_memory.current_goal or 'None'}
- Open loops: {working_memory.open_loops or 'None'}

Output ONLY valid JSON in this exact format:
{{
  "goal": "clear description of what the user wants accomplished",
  "strategy_hint": "optional hint about approach, or null",
  "needs_clarification": false,
  "clarification_question": null
}}

If the request is unclear, set needs_clarification=true and provide a clarification_question.
For simple conversation (greetings, opinions, general knowledge), set goal to the conversational intent.
"""

    messages = [{"role": "system", "content": system_prompt}]
    if recent_memory:
        messages.append({"role": "system", "content": f"=== RECENT MEMORY ===\n{recent_memory}"})
    messages.append({"role": "user", "content": message})

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
        print(f"[Orchestrator] Raw response: {content[:300]}")

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "goal": result.get("goal", message),
                "strategy_hint": result.get("strategy_hint"),
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_question": result.get("clarification_question"),
            }

        # Fallback: treat entire response as a direct goal
        return {
            "goal": message,
            "strategy_hint": None,
            "needs_clarification": False,
            "clarification_question": None,
        }

    except Exception as e:
        print(f"[Orchestrator] Error: {e}")
        # Fallback on error
        return {
            "goal": message,
            "strategy_hint": None,
            "needs_clarification": False,
            "clarification_question": None,
        }
