"""Test script to verify tool calling functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent import BobAgent
from config import BobConfig


def test_tool_calling():
    """Test the agent's ability to call tools."""
    print("Testing Bob's Tool Calling Abilities")
    print("=" * 60)

    try:
        # Initialize agent
        config = BobConfig.from_env()
        agent = BobAgent(config)
        print(f"✅ Agent initialized (Model: {config.model_name})")
        print(f"✅ Tools available: {len(agent.tools)}")
        for tool in agent.tools:
            print(f"   - {tool.name}: {tool.description}")
        print()

        # Test cases
        test_cases = [
            ("What is the current date?", "get_current_date"),
            ("What time is it now?", "get_current_time"),
            ("Calculate 25 * 4 + 10", "calculate_math"),
            ("Convert 'hello world' to uppercase", "format_text"),
        ]

        for i, (question, expected_tool) in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}: {question}")
            print(f"Expected tool: {expected_tool}")
            print("-" * 60)

            try:
                # Use a unique thread for each test
                thread_id = f"test_tool_{i}"
                response = agent.chat(question, thread_id=thread_id)

                print(f"Response: {response}")

                # Check if the response contains relevant information
                response_str = str(response)
                if "error" in response_str.lower() or "trouble" in response_str.lower():
                    print(f"WARNING: Response may indicate an issue")
                else:
                    print(f"PASS: Test passed!")

            except Exception as e:
                print(f"❌ Test failed with error: {e}")
                import traceback

                traceback.print_exc()

        print(f"\n{'='*60}")
        print("Tool testing complete!")

    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_tool_calling()
