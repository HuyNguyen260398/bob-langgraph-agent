"""Custom workflow examples for Bob LangGraph Agent."""

import os
import sys
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bob_langgraph_agent import BobAgent, BobConfig
from bob_langgraph_agent.state import AgentState, create_initial_state, validate_state


class CustomWorkflowAgent(BobAgent):
    """Custom agent with specialized workflow features."""

    def __init__(self, config: BobConfig, workflow_type: str = "standard"):
        """Initialize custom agent.

        Args:
            config: Agent configuration.
            workflow_type: Type of workflow ("standard", "debug", "creative").
        """
        super().__init__(config)
        self.workflow_type = workflow_type

    def custom_process_input(self, state: AgentState) -> Dict[str, Any]:
        """Custom input processing with additional validation."""
        print(f"🔍 [DEBUG] Processing input in {self.workflow_type} mode")

        # Call the parent method
        result = self._process_input(state)

        # Add custom processing
        if self.workflow_type == "debug":
            result["debug_info"] = {
                "input_length": len(state.get("user_input", "")),
                "message_count": len(state.get("messages", [])),
                "processing_mode": self.workflow_type,
            }

        return result

    def creative_response_enhancement(self, state: AgentState) -> Dict[str, Any]:
        """Enhance responses with creative elements."""
        if self.workflow_type == "creative":
            # Add creative prompts to the context
            context = state.get("context", {})
            context["creative_mode"] = True
            context["style_hints"] = [
                "Use analogies and metaphors",
                "Include emojis for engagement",
                "Provide creative examples",
            ]
            return {"context": context}

        return {}


def debug_workflow_example():
    """Example of a debug-enabled workflow."""
    print("=" * 50)
    print("🔸 Debug Workflow Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")

    # Create debug configuration
    debug_config = BobConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
        agent_name="DebugBob",
        system_message="You are DebugBob, an AI assistant that provides detailed explanations of your reasoning process.",
        temperature=0.2,
    )

    # Create custom debug agent
    debug_agent = CustomWorkflowAgent(debug_config, "debug")

    print("🐛 Debug agent created with enhanced logging")
    print("👤 User: Explain how Python decorators work")

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        response = debug_agent.chat("Explain how Python decorators work", "debug_demo")
        print(f"🤖 DebugBob: {response[:200]}...")

        # Show debug information
        analysis = debug_agent.get_conversation_analysis("debug_demo")
        print(f"\n🔍 Debug Info:")
        print(f"   • Messages processed: {analysis.get('total_messages', 0)}")
        print(f"   • Stage: {analysis.get('conversation_stage', 'unknown')}")
    else:
        print("🤖 DebugBob: (Set ANTHROPIC_API_KEY to see debug workflow)")
        print("   This would provide detailed reasoning and debug info")

    print()


def creative_workflow_example():
    """Example of a creative workflow with enhanced responses."""
    print("=" * 50)
    print("🔸 Creative Workflow Example")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")

    # Create creative configuration
    creative_config = BobConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
        agent_name="CreativeBob",
        system_message="""You are CreativeBob, an AI assistant that explains concepts using creative analogies, 
        storytelling, and engaging examples. Make learning fun and memorable!""",
        temperature=0.8,
    )

    # Create custom creative agent
    creative_agent = CustomWorkflowAgent(creative_config, "creative")

    print("🎨 Creative agent with enhanced storytelling")
    print("👤 User: Explain how APIs work")

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        response = creative_agent.chat("Explain how APIs work", "creative_demo")
        print(f"🤖 CreativeBob: {response[:200]}...")
    else:
        print("🤖 CreativeBob: (Set ANTHROPIC_API_KEY to see creative explanations)")
        print("   This would use analogies, stories, and creative examples")

    print()


def specialized_domain_workflow():
    """Example of domain-specific workflow customization."""
    print("=" * 50)
    print("🔸 Specialized Domain Workflow")
    print("=" * 50)

    # DevOps specialist configuration
    devops_config = BobConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
        agent_name="DevOpsExpert",
        system_message="""You are a DevOps Expert specializing in:
        - Infrastructure as Code (Terraform, Ansible)
        - Container orchestration (Kubernetes, Docker Swarm)
        - CI/CD pipelines (Jenkins, GitHub Actions, GitLab CI)
        - Cloud platforms (AWS, Azure, GCP)
        - Monitoring and alerting (Prometheus, Grafana)
        - Security best practices
        
        Always provide practical, production-ready solutions with code examples.""",
        temperature=0.3,
        max_iterations=20,
    )

    # Data Science specialist configuration
    datascience_config = BobConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
        agent_name="DataScienceBot",
        system_message="""You are a Data Science specialist expert in:
        - Machine Learning (scikit-learn, TensorFlow, PyTorch)
        - Data analysis (pandas, numpy, matplotlib)
        - Statistical analysis and hypothesis testing
        - Big data technologies (Spark, Hadoop)
        - MLOps and model deployment
        
        Provide code examples and explain statistical concepts clearly.""",
        temperature=0.4,
    )

    devops_agent = BobAgent(devops_config)
    datascience_agent = BobAgent(datascience_config)

    print("🛠️ Testing specialized agents:")

    # DevOps question
    print("\n👤 User (to DevOps Expert): How do I set up a Kubernetes cluster?")
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        devops_response = devops_agent.chat(
            "How do I set up a Kubernetes cluster?", "devops_demo"
        )
        print(f"🤖 DevOpsExpert: {devops_response[:150]}...")
    else:
        print("🤖 DevOpsExpert: (Would provide K8s setup with kubectl, YAML configs)")

    # Data Science question
    print("\n👤 User (to DataScience Bot): How do I train a neural network?")
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        ds_response = datascience_agent.chat(
            "How do I train a neural network?", "datascience_demo"
        )
        print(f"🤖 DataScienceBot: {ds_response[:150]}...")
    else:
        print(
            "🤖 DataScienceBot: (Would provide NN training with TensorFlow/PyTorch code)"
        )

    print()


def workflow_state_inspection():
    """Example of inspecting and debugging workflow state."""
    print("=" * 50)
    print("🔸 Workflow State Inspection")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    def inspect_state(state: AgentState, node_name: str):
        """Helper to inspect state at different workflow nodes."""
        print(f"🔍 State at {node_name}:")
        print(f"   • Messages: {len(state.get('messages', []))}")
        print(f"   • Iteration: {state.get('iteration_count', 0)}")
        print(f"   • User input: {bool(state.get('user_input'))}")
        print(f"   • Has response: {bool(state.get('agent_response'))}")
        print(f"   • Should end: {state.get('should_end', False)}")

        context = state.get("context", {})
        if context:
            print(f"   • Context keys: {list(context.keys())}")

        metadata = state.get("metadata", {})
        if metadata:
            print(f"   • Conversation ID: {metadata.get('conversation_id', 'N/A')}")
            print(f"   • Total messages: {metadata.get('total_messages', 0)}")

    # Create initial state for inspection
    initial_state = create_initial_state("Test message for state inspection")
    print("📊 Initial State:")
    inspect_state(initial_state, "Initial")

    # Validate state
    is_valid = validate_state(initial_state)
    print(f"✅ State validation: {'Passed' if is_valid else 'Failed'}")

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        print("\n🔄 Running conversation with state inspection...")

        # Have a conversation and inspect final state
        agent.chat("Hello, can you explain state management?", "state_inspection_demo")

        # Get final state (this would require additional access methods)
        print("\n📈 Conversation completed - state updated")
        analysis = agent.get_conversation_analysis("state_inspection_demo")
        print(f"   • Final message count: {analysis.get('total_messages', 0)}")
        print(
            f"   • Conversation stage: {analysis.get('conversation_stage', 'unknown')}"
        )
    else:
        print("\n🔄 (Set ANTHROPIC_API_KEY to see full state inspection)")

    print()


def error_recovery_workflow():
    """Example of error recovery in workflows."""
    print("=" * 50)
    print("🔸 Error Recovery Workflow")
    print("=" * 50)

    # Create configuration with error handling
    config = BobConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
        agent_name="RobustBob",
        system_message="You are RobustBob, designed to handle errors gracefully and provide helpful feedback.",
        max_iterations=5,  # Lower limit to test error handling
    )

    agent = BobAgent(config)

    print("🛡️ Testing error recovery mechanisms:")

    # Test 1: Max iterations
    print("\n1. Testing iteration limits:")
    thread_id = "error_recovery_demo"

    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        try:
            # This should work normally
            response = agent.chat("What is cloud computing?", thread_id)
            print(f"   ✅ Normal operation: Response received")

            # Get analysis to see iteration count
            analysis = agent.get_conversation_analysis(thread_id)
            print(f"   📊 Current iterations: {analysis.get('total_messages', 0)}")

        except Exception as e:
            print(f"   ❌ Error occurred: {e}")
    else:
        print("   (Set ANTHROPIC_API_KEY to test real error recovery)")

    # Test 2: State validation
    print("\n2. Testing state validation:")
    from bob_langgraph_agent.state import validate_state

    # Create invalid state for testing
    invalid_state = {
        "messages": "not a list",  # Should be a list
        "iteration_count": -1,  # Should be non-negative
    }

    is_valid = validate_state(invalid_state)
    print(f"   🔍 Invalid state detected: {'Yes' if not is_valid else 'No'}")

    print()


def custom_memory_workflow():
    """Example of custom memory and persistence patterns."""
    print("=" * 50)
    print("🔸 Custom Memory Workflow")
    print("=" * 50)

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config = BobConfig.from_env()
    agent = BobAgent(config)

    print("🧠 Memory and persistence patterns:")

    # Pattern 1: Session-based conversations
    sessions = ["morning_session", "afternoon_session", "evening_session"]

    for session in sessions:
        print(f"\n📅 {session.replace('_', ' ').title()}:")

        if (
            os.getenv("ANTHROPIC_API_KEY")
            and os.getenv("ANTHROPIC_API_KEY") != "test-key"
        ):
            agent.chat(f"This is my {session.replace('_', ' ')}", session)
            history = agent.get_conversation_history(session)
            print(f"   💬 Messages in {session}: {len(history)}")
        else:
            print(f"   💬 (Would track separate conversation for {session})")

    # Pattern 2: Cross-session memory
    print(f"\n🔗 Cross-session information:")
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "test-key":
        total_sessions = len(sessions)
        total_messages = sum(len(agent.get_conversation_history(s)) for s in sessions)
        print(f"   📊 Total sessions: {total_sessions}")
        print(f"   📊 Total messages across all sessions: {total_messages}")
    else:
        print("   📊 (Would show cross-session analytics)")

    print()


def main():
    """Run all custom workflow examples."""
    print("⚙️ Bob LangGraph Agent - Custom Workflow Examples")
    print("🔧 Set ANTHROPIC_API_KEY for real interactions")
    print()

    try:
        debug_workflow_example()
        creative_workflow_example()
        specialized_domain_workflow()
        workflow_state_inspection()
        error_recovery_workflow()
        custom_memory_workflow()

        print("✅ All custom workflow examples completed!")

    except KeyboardInterrupt:
        print("\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    main()
