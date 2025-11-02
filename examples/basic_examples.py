"""Basic usage examples for Bob LangGraph Agent."""

import os
import sys
import time

# Add the src directory to the path so we can import bob_langgraph_agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bob_langgraph_agent import BobAgent, BobConfig


def basic_chat_example():
    """Basic chat example with single message."""
    print("=" * 50)
    print("🔸 Basic Chat Example")
    print("=" * 50)

    # Set up configuration (you'll need to set ANTHROPIC_API_KEY)
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()

    # Create agent
    agent = BobAgent(config)

    # Simple chat
    print("👤 User: Hello Bob, who are you?")
    print("🤖 Bob:", end=" ")

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        response = agent.chat("Hello Bob, who are you?")
        print(response)
    else:
        print("(Set ANTHROPIC_API_KEY to see real response)")

    print()


def multi_turn_conversation_example():
    """Multi-turn conversation example."""
    print("=" * 50)
    print("🔸 Multi-turn Conversation Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    thread_id = "multi_turn_demo"

    messages = [
        "Hi Bob, I'm working on a Python project.",
        "Can you help me understand LangGraph?",
        "What are the main components I should know about?",
        "Thanks! Can you also tell me about state management?",
    ]

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        for i, message in enumerate(messages, 1):
            print(f"👤 Turn {i}: {message}")
            response = agent.chat(message, thread_id)
            print(f"🤖 Bob: {response}\n")
            time.sleep(1)  # Brief pause between messages
    else:
        for i, message in enumerate(messages, 1):
            print(f"👤 Turn {i}: {message}")
            print("🤖 Bob: (Set ANTHROPIC_API_KEY to see real response)\n")

    print("📊 Conversation History:")
    history = agent.get_conversation_history(thread_id)
    print(f"   Total messages: {len(history)}")
    print()


def tools_usage_example():
    """Example showing tool usage."""
    print("=" * 50)
    print("🔸 Tools Usage Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    # List available tools
    from bob_langgraph_agent.tools import get_tool_descriptions

    tools = get_tool_descriptions()

    print("🛠️ Available Tools:")
    for tool_name, description in tools.items():
        print(f"   • {tool_name}: {description}")
    print()

    # Examples of tool usage
    tool_examples = [
        "What's the current time?",
        "Calculate 25 * 4 + 10",
        "Convert 'hello world' to uppercase",
        "Save a note saying 'Meeting tomorrow at 3 PM' with title 'Reminder'",
    ]

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        for example in tool_examples:
            print(f"👤 User: {example}")
            response = agent.chat(example, "tools_demo")
            print(f"🤖 Bob: {response}\n")
    else:
        for example in tool_examples:
            print(f"👤 User: {example}")
            print("🤖 Bob: (Set ANTHROPIC_API_KEY to see real tool usage)\n")


def conversation_analysis_example():
    """Example showing conversation analysis features."""
    print("=" * 50)
    print("🔸 Conversation Analysis Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    thread_id = "analysis_demo"

    # Simulate a conversation
    conversation = [
        "Hi Bob, I need help with my DevOps setup",
        "I'm using Docker and Kubernetes",
        "My main issue is with CI/CD pipeline configuration",
        "Specifically, I'm having trouble with GitHub Actions",
        "The build is failing on the test stage",
        "Can you help me debug this?",
    ]

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        # Have the conversation
        for message in conversation:
            agent.chat(message, thread_id)

        # Get analysis
        print("📊 Conversation Analysis:")
        analysis = agent.get_conversation_analysis(thread_id)
        print(f"   Stage: {analysis.get('conversation_stage', 'Unknown')}")
        print(f"   Total messages: {analysis.get('total_messages', 0)}")
        print(f"   User messages: {analysis.get('user_messages', 0)}")
        print(f"   AI messages: {analysis.get('ai_messages', 0)}")
        print(
            f"   Duration: {analysis.get('conversation_length_minutes', 'Unknown')} minutes"
        )

        recent_topics = analysis.get("recent_topics", [])
        if recent_topics:
            print(f"   Recent topics: {', '.join(recent_topics[-3:])}")

        print("\n📝 Conversation Summary:")
        summary = agent.get_conversation_summary(thread_id)
        print(f"   {summary}")
    else:
        print("📊 Conversation Analysis:")
        print("   (Set ANTHROPIC_API_KEY to see real analysis)")
        print("   This would show conversation stage, message counts, duration, etc.")

        print("\n📝 Conversation Summary:")
        print("   (Set ANTHROPIC_API_KEY to see real summary)")

    print()


def configuration_example():
    """Example showing different configuration options."""
    print("=" * 50)
    print("🔸 Configuration Example")
    print("=" * 50)

    # Example 1: From environment
    print("🔧 Configuration from environment:")
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    os.environ["AGENT_NAME"] = "CustomBob"
    os.environ["TEMPERATURE"] = "0.9"

    config1 = BobConfig.from_env()
    print(f"   Agent name: {config1.agent_name}")
    print(f"   Temperature: {config1.temperature}")
    print(f"   Model: {config1.model_name}")

    # Example 2: Programmatic configuration
    print("\n🔧 Programmatic configuration:")
    config2 = BobConfig(
        anthropic_api_key="test-key-2",
        agent_name="DevOpsBuddy",
        temperature=0.5,
        max_iterations=15,
        system_message="You are DevOpsBuddy, specialized in DevOps and infrastructure.",
    )
    print(f"   Agent name: {config2.agent_name}")
    print(f"   Temperature: {config2.temperature}")
    print(f"   Max iterations: {config2.max_iterations}")
    print(f"   System message: {config2.system_message[:50]}...")

    print()


def error_handling_example():
    """Example showing error handling."""
    print("=" * 50)
    print("🔸 Error Handling Example")
    print("=" * 50)

    print("🚨 Testing various error conditions:")

    # Test 1: Missing API key
    print("\n1. Missing API key:")
    try:
        config = BobConfig(anthropic_api_key=None)
        print("   ❌ Should have failed!")
    except ValueError as e:
        print(f"   ✅ Caught expected error: {e}")

    # Test 2: Invalid configuration
    print("\n2. Invalid temperature:")
    try:
        config = BobConfig(
            anthropic_api_key="test-key", temperature=2.5  # Should be between 0 and 1
        )
        print("   ✅ Configuration created (validation could be added)")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

    # Test 3: Agent with invalid config
    print("\n3. Agent initialization:")
    try:
        config = BobConfig(anthropic_api_key="test-key")
        agent = BobAgent(config)
        print("   ✅ Agent created successfully")
    except Exception as e:
        print(f"   ❌ Error creating agent: {e}")

    print()


def main():
    """Run all examples."""
    print("🤖 Bob LangGraph Agent - Examples")
    print("🔧 Make sure to set ANTHROPIC_API_KEY for real interactions")
    print()

    try:
        basic_chat_example()
        multi_turn_conversation_example()
        tools_usage_example()
        conversation_analysis_example()
        configuration_example()
        error_handling_example()

        print("✅ All examples completed!")

    except KeyboardInterrupt:
        print("\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    main()
