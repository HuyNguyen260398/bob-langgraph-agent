"""Simple test script to verify agent functionality."""

import logging
from src.bob_langgraph_agent import BobAgent, BobConfig

# Enable INFO level logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def test_simple_chat():
    """Test a simple chat interaction."""
    try:
        # Create configuration
        config = BobConfig.from_env()
        print(f"[OK] Loaded configuration (Model: {config.model_name})")

        # Create agent
        agent = BobAgent(config)
        print("[OK] Agent initialized successfully!")

        # Test simple message
        print("\n" + "=" * 50)
        user_message = "hi"
        print(f"User: {user_message}")

        response = agent.chat(user_message, thread_id="test_session")
        print(f"Bob Response Type: {type(response)}")
        print(f"Bob Response Value: {repr(response)}")
        print(f"Bob: {response}")
        print("=" * 50)

        print("\n[OK] Test completed successfully!")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_simple_chat()
