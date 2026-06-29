"""
friday.cognition.reflector — Runs after critic passes.
Writes to memory. Never responds to user.

Actions:
1. Append episode to episodic memory (task, tools, outcome, lesson)
2. Call update_strategy() in procedural memory (success or failure)
3. Propose candidate belief to semantic memory if lesson is strong

Never touches synthesizer, never reads working memory snapshot as truth.
"""

import datetime
from friday.memory import episodic, procedural, semantic
from friday.memory.episodic import Episode


def reflect(goal: str, observations: list, outcome: str, strategy_used: str = None):
    """
    Input: goal, observations, outcome ("success"/"failure"), strategy_used
    Never returns anything user-facing.
    """
    now = datetime.datetime.now().isoformat()

    # 1. Extract tools used from observations
    tools_used = []
    for obs in observations:
        if obs.startswith("[") and "]" in obs:
            tool_name = obs[1:obs.index("]")]
            if tool_name not in tools_used and not tool_name.startswith("Executor"):
                tools_used.append(tool_name)

    # 2. Generate a lesson from the outcome
    if outcome == "success":
        lesson = f"Successfully completed: {goal}"
        if strategy_used:
            lesson += f" using strategy '{strategy_used}'"
    else:
        lesson = f"Failed to complete: {goal}"
        if observations:
            # Include last observation as context
            last_obs = observations[-1][:200] if observations[-1] else ""
            lesson += f". Last observation: {last_obs}"

    # 3. Append episode to episodic memory
    episode = Episode(
        task=goal,
        tools_used=tools_used,
        outcome=outcome,
        lesson=lesson,
        timestamp=now,
    )
    try:
        episodic.append_episode(episode)
        print(f"[Reflector] Episode recorded: {outcome} - {goal[:80]}")
    except Exception as e:
        print(f"[Reflector] Failed to record episode: {e}")

    # 4. Update strategy in procedural memory
    if strategy_used:
        try:
            procedural.update_strategy(strategy_used, success=(outcome == "success"))
            print(f"[Reflector] Strategy '{strategy_used}' updated: {outcome}")
        except Exception as e:
            print(f"[Reflector] Failed to update strategy: {e}")

    # 5. Propose candidate belief if lesson is strong
    if outcome == "success" and tools_used:
        # Propose a belief about what tools work for what tasks
        belief_statement = f"For tasks involving '{goal[:50]}', tools [{', '.join(tools_used[:3])}] are effective."
        try:
            semantic.propose_belief(belief_statement, confidence=0.6)
            semantic.promote_to_semantic()  # Check if any candidates qualify
            print(f"[Reflector] Belief proposed: {belief_statement[:80]}")
        except Exception as e:
            print(f"[Reflector] Failed to propose belief: {e}")
