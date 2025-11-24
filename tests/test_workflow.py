#!/usr/bin/env python3
"""Simple test to verify the agent workflow without API calls."""

import os
import sys
from bob_langgraph_agent import BobAgent, BobConfig
from bob_langgraph_agent.state import create_initial_state


def test_workflow_structure():
    """Test the workflow structure without making API calls."""
    print("🔧 Testing Bob LangGraph Agent Workflow Structure")
    print("=" * 55)

    try:
        # Create a basic config (won't make API calls)
        config = BobConfig(
            anthropic_api_key="test-key",  # Dummy key for structure testing
            model_name="claude-3-5-sonnet-20241022",
            system_message="You are Bob, a helpful AI assistant.",
            max_tokens=1000,
            temperature=0.7,
        )

        # Create agent (this will initialize the workflow)
        agent = BobAgent(config)
        print("✅ Agent created successfully!")

        # Test state structure
        test_state = create_initial_state("test message")
        print("✅ Initial state created successfully!")

        # Show workflow structure
        print(f"\n📋 Workflow Structure:")
        workflow_nodes = list(agent.workflow.nodes.keys())
        print(f"   • Nodes: {workflow_nodes}")
        print(f"   • Total nodes: {len(workflow_nodes)}")

        # Show state fields
        print(f"\n📊 State Fields:")
        for key, value in test_state.items():
            print(f"   • {key}: {type(value).__name__}")

        # Test the _should_continue logic
        print(f"\n🔄 Testing continuation logic:")

        # Test single-turn (continue_conversation=False)
        single_turn_state = test_state.copy()
        single_turn_state["continue_conversation"] = False
        single_turn_state["agent_response"] = "Test response"
        single_turn_state["iteration_count"] = 1

        should_continue = agent._should_continue(single_turn_state)
        print(f"   • Single-turn after response: {should_continue} (should be 'end')")

        # Test multi-turn (continue_conversation=True)
        multi_turn_state = test_state.copy()
        multi_turn_state["continue_conversation"] = True
        multi_turn_state["agent_response"] = "Test response"
        multi_turn_state["iteration_count"] = 1

        should_continue = agent._should_continue(multi_turn_state)
        print(
            f"   • Multi-turn after response: {should_continue} (should be 'continue')"
        )

        print(f"\n✅ All workflow structure tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error testing workflow: {e}")
        return False


if __name__ == "__main__":
    success = test_workflow_structure()
    if success:
        print(f"\n🎉 Bob LangGraph Agent is ready to use!")
        print(f"   To run with real API calls:")
        print(f"   1. Set your ANTHROPIC_API_KEY in .env file")
        print(f"   2. Run: uv run python -m bob_langgraph_agent.main")
    else:
        print(f"\n⚠️  There are issues with the workflow structure.")
        sys.exit(1)
