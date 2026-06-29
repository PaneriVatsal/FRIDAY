"""
friday.cli — Simple CLI loop for FRIDAY.
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from friday.agent import FridayAgent


def main():
    agent = FridayAgent()
    print("FRIDAY CLI — Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            message = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if message.strip().lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        if not message.strip():
            continue

        response = agent.chat(message)
        print(f"FRIDAY: {response}\n")


if __name__ == "__main__":
    main()
