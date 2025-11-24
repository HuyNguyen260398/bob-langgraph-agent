"""Main entry point for Bob LangGraph Agent."""

import os
import sys
from typing import Optional

from agent import BobAgent
from config import BobConfig


def print_streaming_response(agent: BobAgent, user_input: str, thread_id: str):
    """Print streaming response from the agent.

    Args:
        agent: The Bob agent instance.
        user_input: User's input message.
        thread_id: Thread identifier for the conversation.
    """
    # Use regular chat instead of streaming for simplicity
    # Streaming was causing issues with the workflow loop
    try:
        print("🤔 Bob is thinking...", end="", flush=True)
        response = agent.chat(user_input, thread_id)
        print(f"\r🤖 Bob: {response}")
    except Exception as e:
        print(f"\r❌ Error: {e}")


def main():
    """Main function to run the Bob LangGraph Agent."""
    print("🤖 Bob LangGraph Agent - Your AI Operations Buddy!")
    print("=" * 50)

    try:
        # Create configuration
        config = BobConfig.from_env()
        print(f"✅ Loaded configuration (Model: {config.model_name})")

        # Create agent
        agent = BobAgent(config)
        print("✅ Agent initialized successfully!")

        # Interactive chat loop
        print("\n💬 Starting interactive chat (type 'quit' to exit)")
        print("-" * 50)

        thread_id = "interactive_session"

        while True:
            try:
                user_input = input("\n👤 You: ").strip()

                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("👋 Goodbye! Thanks for chatting with Bob!")
                    break

                if not user_input:
                    continue

                # Use streaming response
                print_streaming_response(agent, user_input, thread_id)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for chatting with Bob!")
                break
            except Exception as e:
                print(f"❌ Error during chat: {e}")
                continue

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print(
            "\n📝 Please make sure to set your ANTHROPIC_API_KEY environment variable."
        )
        print("   You can do this by:")
        print("   1. Creating a .env file with: ANTHROPIC_API_KEY=your_key_here")
        print(
            "   2. Or setting it in your shell: export ANTHROPIC_API_KEY=your_key_here"
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def demo_chat(message: Optional[str] = None):
    """Demo function to show basic agent usage.

    Args:
        message: Optional message to send to the agent.
    """
    try:
        config = BobConfig.from_env()
        agent = BobAgent(config)

        if message is None:
            message = "Hello Bob! Can you introduce yourself?"

        print(f"👤 User: {message}")
        response = agent.chat(message)
        print(f"🤖 Bob: {response}")

    except Exception as e:
        print(f"❌ Error in demo: {e}")


if __name__ == "__main__":
    main()
