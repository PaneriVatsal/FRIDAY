"""
friday.cognition.executor — Uses qwen2.5-coder:latest to run tool calls.
Receives plan steps and executes them using TOOLS_DEFINITION from tools/registry.py.
After each tool call, appends result to working_memory.observations.
Max 5 tool call turns.
Returns list of raw observations (str).
Never summarizes, never reasons about goal completion. Just executes and collects.
"""

import json
import re
import requests
from friday.tools.registry import TOOLS_DEFINITION
from friday.tools.dispatcher import dispatch_tool

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5-coder:latest"


def execute(steps: list, working_memory) -> list:
    """
    Execute plan steps using qwen2.5-coder with tool calling.
    Appends results to working_memory.observations.
    Returns list of raw observation strings.
    """
    observations = []

    # Build the execution prompt
    steps_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))

    system_prompt = f"""You are FRIDAY's execution engine. Execute the following plan steps using the available tools.
Call tools as needed. You may chain up to 5 tool calls. Return results clearly.
Never explain what you are going to do. Just do it.

Plan steps:
{steps_text}
"""

    # Valid tool names for manual parsing
    valid_tool_names = [t["function"]["name"] for t in TOOLS_DEFINITION]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Execute these steps now: {steps_text}"}
    ]

    max_turns = 5
    last_tool_output = None

    for turn in range(max_turns):
        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "tools": TOOLS_DEFINITION,
            "options": {"num_predict": -1}
        }
        try:
            res = requests.post(OLLAMA_URL, json=payload, timeout=60)
            res.raise_for_status()
            msg = res.json().get("message", {})
            content = msg.get("content", "").strip()
            tool_calls = msg.get("tool_calls", [])
            print(f"[Executor] Turn {turn+1} tool_calls: {tool_calls}")

            # Try to parse manual JSON tool calls from text
            manual_tools = []
            if not tool_calls and content:
                json_blocks = []
                brace_level = 0
                current_block = ""
                in_string = False
                escape_next = False

                for char in content:
                    if escape_next:
                        current_block += char
                        escape_next = False
                        continue

                    if char == '"':
                        in_string = not in_string
                    elif char == '\\':
                        escape_next = True

                    if not in_string:
                        if char == '{':
                            brace_level += 1
                        elif char == '}':
                            brace_level -= 1

                    if brace_level > 0 or (char == '}' and brace_level == 0 and current_block):
                        current_block += char
                        if brace_level == 0:
                            json_blocks.append(current_block)
                            current_block = ""

                for block in json_blocks:
                    try:
                        data = json.loads(block)
                        if isinstance(data, dict) and data.get("name") in valid_tool_names:
                            manual_tools.append(data)
                    except json.JSONDecodeError:
                        pass

            if tool_calls:
                messages.append(msg)
                for tc in tool_calls:
                    name = tc["function"]["name"]
                    args = tc["function"]["arguments"]
                    print(f"[Tool] {name}({args})")
                    output = dispatch_tool(name, args)
                    print(f"[Output] {output[:200]}")
                    observations.append(f"[{name}] {output}")
                    working_memory.observations.append(f"[{name}] {output}")
                    last_tool_output = output
                    messages.append({"role": "tool", "content": output})
                continue
            elif manual_tools:
                messages.append(msg)
                combined_outputs = []
                for tool in manual_tools:
                    name = tool.get("name")
                    args = tool.get("arguments") or tool.get("parameters") or {}
                    print(f"[Tool Manual] {name}({args})")
                    output = dispatch_tool(name, args)
                    print(f"[Output] {output[:200]}")
                    observations.append(f"[{name}] {output}")
                    working_memory.observations.append(f"[{name}] {output}")
                    last_tool_output = output
                    combined_outputs.append(f"Tool '{name}' output:\n{output}")

                messages.append({
                    "role": "user",
                    "content": "\n\n".join(combined_outputs) + "\n\nIf all steps are complete, respond in plain text. If more tools are needed, call the next tool now."
                })
                continue
            else:
                # No tool calls — executor is done
                if content:
                    observations.append(content)
                    working_memory.observations.append(content)
                elif last_tool_output:
                    # Already captured
                    pass
                break

        except Exception as e:
            error_msg = f"[Executor Error] Turn {turn+1}: {str(e)}"
            print(error_msg)
            observations.append(error_msg)
            working_memory.observations.append(error_msg)
            break

    return observations
