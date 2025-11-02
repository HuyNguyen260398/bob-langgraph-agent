"""Advanced usage examples for Bob LangGraph Agent."""

import os
import sys
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bob_langgraph_agent import BobAgent, BobConfig


def streaming_chat_example():
    """Example of streaming chat responses."""
    print("=" * 50)
    print("🔸 Streaming Chat Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    print("👤 User: Explain how LangGraph works in detail")
    print("🤖 Bob (streaming):", end=" ")

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        try:
            for update in agent.stream_chat(
                "Explain how LangGraph works in detail", "streaming_demo"
            ):
                if "agent_response" in update:
                    response = update["agent_response"]
                    if hasattr(response, "content"):
                        print(".", end="", flush=True)  # Show streaming progress
            print(" [Streaming complete]")
        except Exception as e:
            print(f"(Streaming error: {e})")
    else:
        print("(Set ANTHROPIC_API_KEY to see real streaming)")

    print()


def multi_threaded_chat_example():
    """Example of handling multiple conversations concurrently."""
    print("=" * 50)
    print("🔸 Multi-threaded Chat Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    def chat_worker(thread_id: str, question: str) -> str:
        """Worker function for threaded chat."""
        try:
            if (
                os.getenv("ANTHROPIC_API_KEY")
                and os.getenv("ANTHROPIC_API_KEY") != "test-key"
            ):
                response = agent.chat(question, thread_id)
                return f"Thread {thread_id}: {response[:100]}..."
            else:
                return f"Thread {thread_id}: (Mock response for: {question})"
        except Exception as e:
            return f"Thread {thread_id}: Error - {e}"

    # Simulate multiple users asking questions
    conversations = [
        ("user_1", "What is Docker?"),
        ("user_2", "How do I set up Kubernetes?"),
        ("user_3", "Explain CI/CD pipelines"),
        ("user_4", "What are microservices?"),
    ]

    print("🔄 Running multiple conversations concurrently...")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(chat_worker, thread_id, question)
            for thread_id, question in conversations
        ]

        for future in futures:
            result = future.result()
            print(f"   {result}")

    print()


def custom_workflow_example():
    """Example of customizing the agent's behavior."""
    print("=" * 50)
    print("🔸 Custom Workflow Example")
    print("=" * 50)

    # Create specialized DevOps agent
    devops_config = BobConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
        agent_name="DevOpsBuddy",
        temperature=0.3,  # More focused responses
        system_message="""You are DevOpsBuddy, a specialized AI assistant for DevOps engineers.
        You excel at:
        - Infrastructure as Code (Terraform, CloudFormation)
        - Container orchestration (Docker, Kubernetes)
        - CI/CD pipelines (GitHub Actions, Jenkins, GitLab CI)
        - Cloud platforms (AWS, Azure, GCP)
        - Monitoring and observability
        
        Always provide practical, actionable advice with code examples when relevant.""",
        max_iterations=15,
    )

    devops_agent = BobAgent(devops_config)

    print("🛠️ DevOps-specialized agent created")
    print("👤 User: I need help setting up a Kubernetes deployment")

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        response = devops_agent.chat(
            "I need help setting up a Kubernetes deployment", "devops_demo"
        )
        print(f"🤖 DevOpsBuddy: {response[:200]}...")
    else:
        print("🤖 DevOpsBuddy: (Set ANTHROPIC_API_KEY to see specialized response)")

    print()


def conversation_persistence_example():
    """Example showing conversation persistence across sessions."""
    print("=" * 50)
    print("🔸 Conversation Persistence Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()

    # Session 1
    print("📱 Session 1:")
    agent1 = BobAgent(config)
    thread_id = "persistent_demo"

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        response1 = agent1.chat("My name is Alice and I work at TechCorp", thread_id)
        print(f"👤 User: My name is Alice and I work at TechCorp")
        print(f"🤖 Bob: {response1[:100]}...")

        # Session 2 (new agent instance, same thread)
        print("\n📱 Session 2 (same thread, new agent instance):")
        agent2 = BobAgent(config)
        response2 = agent2.chat("What's my name and where do I work?", thread_id)
        print(f"👤 User: What's my name and where do I work?")
        print(f"🤖 Bob: {response2[:100]}...")

        # Show history
        print(
            f"\n📚 Total conversation history: {len(agent2.get_conversation_history(thread_id))} messages"
        )
    else:
        print("👤 User: My name is Alice and I work at TechCorp")
        print("🤖 Bob: (Set ANTHROPIC_API_KEY to see persistence in action)")
        print("\n📱 Session 2 would remember Alice from TechCorp")

    print()


def tool_chaining_example():
    """Example of chaining multiple tool calls."""
    print("=" * 50)
    print("🔸 Tool Chaining Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    complex_request = """Can you help me with these tasks:
    1. Get the current time
    2. Calculate 15 * 8 + 25
    3. Convert the result to uppercase text format
    4. Save all this information in a note titled 'Daily Calculations'"""

    print("👤 User: Complex multi-tool request:")
    print(f"   {complex_request}")
    print()

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        response = agent.chat(complex_request, "tool_chaining_demo")
        print(f"🤖 Bob: {response}")
    else:
        print("🤖 Bob: (Set ANTHROPIC_API_KEY to see tool chaining)")
        print("   This would call multiple tools in sequence:")
        print("   • get_current_time()")
        print("   • calculate_math('15 * 8 + 25')")
        print("   • format_text(result, 'upper')")
        print("   • save_note(content, 'Daily Calculations')")

    print()


def conversation_analysis_deep_dive():
    """Deep dive into conversation analysis features."""
    print("=" * 50)
    print("🔸 Deep Conversation Analysis")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    # Create a detailed conversation
    thread_id = "analysis_deep_dive"
    conversation_flow = [
        ("user", "Hi, I'm starting a new project"),
        ("user", "It's a web application using React and Node.js"),
        ("user", "I need help with the database design"),
        ("user", "We're considering PostgreSQL vs MongoDB"),
        ("user", "The app will handle user authentication"),
        ("user", "And we need real-time features like chat"),
        ("user", "What database would you recommend?"),
        ("user", "Also, how should we handle the real-time features?"),
        ("user", "Performance is really important for us"),
        ("user", "We expect about 10,000 users initially"),
    ]

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        print("🗣️ Simulating detailed conversation...")
        for speaker, message in conversation_flow:
            if speaker == "user":
                agent.chat(message, thread_id)

        print("\n📊 Detailed Analysis:")
        analysis = agent.get_conversation_analysis(thread_id)

        print(f"   📈 Conversation Metrics:")
        print(f"      • Stage: {analysis.get('conversation_stage', 'unknown')}")
        print(f"      • Total messages: {analysis.get('total_messages', 0)}")
        print(f"      • User messages: {analysis.get('user_messages', 0)}")
        print(f"      • AI responses: {analysis.get('ai_messages', 0)}")
        print(
            f"      • Duration: {analysis.get('conversation_length_minutes', 'unknown')} minutes"
        )
        print(f"      • Needs summary: {analysis.get('needs_summary', False)}")

        recent_topics = analysis.get("recent_topics", [])
        if recent_topics:
            print(f"   🎯 Recent Topics:")
            for i, topic in enumerate(recent_topics[-5:], 1):
                print(f"      {i}. {topic[:60]}...")

        print(f"\n📝 Generated Summary:")
        summary = agent.get_conversation_summary(thread_id)
        print(f"   {summary}")

    else:
        print("🗣️ This would simulate a 10-message conversation about:")
        print("   • Web app development")
        print("   • Database selection")
        print("   • Real-time features")
        print("   • Performance considerations")
        print("\n📊 Analysis would include:")
        print("   • Conversation metrics and stage")
        print("   • Topic tracking and evolution")
        print("   • Automatic summarization")
        print("   • Performance insights")

    print()


def performance_monitoring_example():
    """Example of monitoring agent performance."""
    print("=" * 50)
    print("🔸 Performance Monitoring Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    print("⏱️ Measuring response times and token usage...")

    test_queries = [
        "What is Python?",
        "Explain machine learning",
        "How do I deploy a web app?",
        "What are best practices for code review?",
    ]

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        total_time = 0
        for i, query in enumerate(test_queries, 1):
            start_time = time.time()
            response = agent.chat(query, f"perf_test_{i}")
            end_time = time.time()

            response_time = end_time - start_time
            total_time += response_time

            print(f"   Query {i}: {response_time:.2f}s - {len(response)} chars")

        avg_time = total_time / len(test_queries)
        print(f"\n📊 Performance Summary:")
        print(f"   • Average response time: {avg_time:.2f}s")
        print(f"   • Total time: {total_time:.2f}s")
        print(f"   • Queries processed: {len(test_queries)}")

    else:
        print("   (Set ANTHROPIC_API_KEY to see real performance metrics)")
        print("   This would measure:")
        print("   • Response times per query")
        print("   • Token usage estimation")
        print("   • Average performance metrics")

    print()


def main():
    """Run all advanced examples."""
    print("🚀 Bob LangGraph Agent - Advanced Examples")
    print("🔧 Set ANTHROPIC_API_KEY for real interactions")
    print()

    try:
        streaming_chat_example()
        multi_threaded_chat_example()
        custom_workflow_example()
        conversation_persistence_example()
        tool_chaining_example()
        conversation_analysis_deep_dive()
        performance_monitoring_example()

        print("✅ All advanced examples completed!")

    except KeyboardInterrupt:
        print("\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    main()
