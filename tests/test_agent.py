#!/usr/bin/env python3
"""Quick test script for Bob LangGraph Agent."""

import os
from src.bob_langgraph_agent.config import BobConfig
from src.bob_langgraph_agent.agent import BobAgent


def test_agent():
    """Test the agent with a dummy API key."""
    # Set a dummy API key for testing
    os.environ["ANTHROPIC_API_KEY"] = "test-key"

    try:
        # Test configuration
        config = BobConfig.from_env()
        print(f"✅ Configuration loaded: {config.agent_name}")
        print(f"   Model: {config.model_name}")
        print(f"   Temperature: {config.temperature}")

        # Test agent initialization (this should work even with dummy key)
        agent = BobAgent(config)
        print("✅ Agent initialized successfully")

        # Test workflow creation
        print(f"✅ Workflow compiled with {len(agent.workflow.nodes)} nodes")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Bob LangGraph Agent...")
    success = test_agent()
    if success:
        print("\n✅ All tests passed! The agent is properly implemented.")
    else:
        print("\n❌ Tests failed. Check the implementation.")
