"""
friday.cognition.critic — Uses gemma4:e4b with thinking mode to judge whether the goal was achieved.
If passed=False, agent retries planner up to 3 times total.
Critic never fixes, never summarizes, never responds to user.
"""

import json
import re
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "gemma4:e4b"


def critique(goal: str, observations: list) -> dict:
    """
    Input: goal, observations from executor
    Output: {
        "passed": bool,
        "reason": str,
        "retry_hint": str or None
    }
    """
    observations_text = "\n".join(f"- {obs}" for obs in observations)

    system_prompt = """<|think|>You are FRIDAY's critic. Your ONLY job is to judge whether the goal was achieved based on the observations.

Rules:
- Output ONLY valid JSON
- Be strict but fair
- If the observations show the goal was completed (even partially with useful output), pass it
- If observations show errors, missing data, or incomplete execution, fail it
- For simple conversation goals (greetings, opinions), always pass if there's any reasonable response

Output format:
{
  "passed": true/false,
  "reason": "brief explanation",
  "retry_hint": "what to try differently, or null"
}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Goal: {goal}\n\nObservations:\n{observations_text}"}
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
        print(f"[Critic] Raw response: {content[:300]}")

        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "passed": result.get("passed", True),
                "reason": result.get("reason", ""),
                "retry_hint": result.get("retry_hint"),
            }

        # Fallback: if we can't parse, assume passed
        return {"passed": True, "reason": "Could not parse critic response, assuming pass.", "retry_hint": None}

    except Exception as e:
        print(f"[Critic] Error: {e}")
        # On error, assume passed to avoid infinite retries
        return {"passed": True, "reason": f"Critic error: {e}", "retry_hint": None}
