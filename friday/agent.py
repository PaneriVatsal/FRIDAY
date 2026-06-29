"""
friday.agent — FridayAgent is the cognitive loop. Coordinates all modules in order.
No business logic lives here. Just coordination.
"""

from friday.identity import load_identity
from friday.memory.working import WorkingMemory
from friday.memory.vault_log import load_recent_memory
from friday.cognition.orchestrator import orchestrate
from friday.cognition.planner import plan
from friday.cognition.executor import execute
from friday.cognition.critic import critique
from friday.cognition.reflector import reflect
from friday.cognition.synthesizer import synthesize, SynthesisContext


class FridayAgent:
    def __init__(self):
        self.identity = load_identity()

    def chat(self, message: str) -> str:
        """
        Full cognitive loop:
        1. Load identity
        2. Fresh working memory (RAM only)
        3. Load recent memory from vault
        4. Orchestrator → goal
        5. Planner → steps
        6. Executor → observations
        7. Critic → pass/fail (retry up to 3 times)
        8. Reflector → update memory
        9. Clear working memory, snapshot to debug
        10. Synthesizer → response
        """
        # 1. Identity (already loaded in __init__, reload for freshness)
        identity = self.identity

        # 2. Fresh working memory
        working_memory = WorkingMemory()

        # 3. Load recent memory
        recent_memory = load_recent_memory(20)

        # 4. Orchestrator
        print(f"\n[Agent] === New request: {message[:80]} ===")
        orch_result = orchestrate(message, identity, working_memory, recent_memory)
        goal = orch_result["goal"]
        strategy_hint = orch_result.get("strategy_hint")
        working_memory.current_goal = goal
        print(f"[Agent] Goal: {goal}")

        # If needs clarification, return immediately
        if orch_result.get("needs_clarification"):
            question = orch_result.get("clarification_question", "Could you clarify?")
            print(f"[Agent] Clarification needed: {question}")
            return question

        # 5-7. Plan → Execute → Critique loop (max 3 retries)
        max_retries = 3
        observations = []
        strategy_used = None
        outcome = "failure"

        for attempt in range(max_retries):
            # 5. Planner
            plan_result = plan(goal, strategy_hint)
            steps = plan_result["steps"]
            strategy_used = plan_result.get("strategy_used")
            working_memory.current_plan = steps
            print(f"[Agent] Plan (attempt {attempt+1}): {steps}")

            # 6. Executor
            observations = execute(steps, working_memory)
            print(f"[Agent] Observations count: {len(observations)}")

            # 7. Critic
            critic_result = critique(goal, observations)
            print(f"[Agent] Critic: passed={critic_result['passed']}, reason={critic_result.get('reason', '')[:100]}")

            if critic_result["passed"]:
                outcome = "success"
                break
            else:
                # Retry with hint from critic
                retry_hint = critic_result.get("retry_hint")
                if retry_hint:
                    strategy_hint = retry_hint
                    print(f"[Agent] Retrying with hint: {retry_hint}")
                # Clear observations for next attempt
                working_memory.observations = []

        # 8. Reflector (always runs, even on failure)
        try:
            reflect(goal, observations, outcome, strategy_used)
        except Exception as e:
            print(f"[Agent] Reflector error: {e}")

        # 9. Clear working memory, snapshot to debug
        working_memory.snapshot()
        working_memory.clear()

        # 10. Synthesizer
        if outcome == "success":
            context = SynthesisContext(
                goal=goal,
                verified_observations=observations,
                identity_voice=f"{identity.personality}, {identity.communication_style}",
            )
            response = synthesize(context)
        else:
            # Synthesize honest failure response
            context = SynthesisContext(
                goal=goal,
                verified_observations=observations + [f"[FAILED after {max_retries} attempts]"],
                identity_voice=f"{identity.personality}, {identity.communication_style}",
            )
            response = synthesize(context)

        print(f"[Agent] Response length: {len(response)}")
        return response
