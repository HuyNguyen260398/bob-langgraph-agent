"""Simple debug script to trace tool execution."""

import sys
import os
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent import BobAgent
from config import BobConfig


def simple_tool_test():
    """Simple test with detailed logging."""
    print("\n" + "=" * 60)
    print("SIMPLE TOOL TEST - What is the current date?")
    print("=" * 60 + "\n")

    config = BobConfig.from_env()
    agent = BobAgent(config)

    question = "What is the current date?"
    print(f"Question: {question}\n")

    try:
        response = agent.chat(question, thread_id="debug_test")
        print(f"\n{'='*60}")
        print(f"FINAL RESPONSE:")
        print(f"Type: {type(response)}")
        print(f"Value: {response}")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    simple_tool_test()
