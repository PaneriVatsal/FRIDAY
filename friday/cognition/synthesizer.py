"""
friday.cognition.synthesizer — The ONLY module that produces user-facing responses.
Receives a frozen SynthesisContext only.
Has no access to planner, critic, reflector, or dispatcher.
Uses gemma4:e4b to transform goal + verified observations into a clean, natural response.
Never decides steps. Never judges success. Never updates memory.
"""

import json
import re
import requests
from dataclasses import dataclass
from typing import List

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "gemma4:e4b"


@dataclass(frozen=True)
class SynthesisContext:
    goal: str
    verified_observations: List[str]
    identity_voice: str


def synthesize(context: SynthesisContext) -> str:
    """
    Transform goal + verified observations into a clean, natural response.
    This is the ONLY module that produces user-facing text.
    """
    observations_text = "\n".join(f"- {obs}" for obs in context.verified_observations)

    system_prompt = f"""You are FRIDAY, a Jarvis-style AI assistant.
You are given the user's goal and the execution results.
Synthesize a clear, concise, intelligent response for the user.

Voice: {context.identity_voice}

Rules:
- Do not mention internal systems, tool names, or JSON
- Respond naturally as if you did the work yourself
- Be concise unless detail is needed
- If results include data (weather, battery, search results), present them clearly
- If results include file paths or screenshots, include them naturally
- Never say "I used the web_search tool" — just present the information
"""

    user_content = f"""User's goal: {context.goal}

Execution results:
{observations_text}

Respond naturally to the user."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
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
        response = res.json().get("message", {}).get("content", "").strip()
        print(f"[Synthesizer] Response length: {len(response)}")

        # Fix screenshot IMG path if present
        for obs in context.verified_observations:
            if "[IMG]" in obs:
                img_match = re.search(r'\[IMG\](\S+)', obs)
                if img_match:
                    actual_img = img_match.group(1)
                    response = re.sub(r'\[IMG\]\S+', '', response).strip()
                    response += f"\n[IMG]{actual_img}"

        return response if response else "I completed the task but couldn't generate a summary."

    except Exception as e:
        print(f"[Synthesizer] Error: {e}")
        # Fallback: return raw observations
        if context.verified_observations:
            return "\n".join(context.verified_observations)
        return f"I encountered an issue while processing your request: {str(e)}"
