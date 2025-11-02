#!/usr/bin/env python3
"""Test script for error handling features in Bob LangGraph Agent."""

import os
import sys
import time
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.bob_langgraph_agent.config import BobConfig
from src.bob_langgraph_agent.agent import BobAgent
from src.bob_langgraph_agent.error_handling import (
    ErrorHandler,
    RetryConfig,
    GracefulDegradation,
    ErrorType,
)


def test_error_classification():
    """Test error classification functionality."""
    print("🔍 Testing Error Classification...")

    error_handler = ErrorHandler()

    # Test different error types
    test_cases = [
        (Exception("API rate limit exceeded"), ErrorType.RATE_LIMIT),
        (Exception("Connection timeout"), ErrorType.NETWORK_ERROR),
        (ValueError("Invalid value provided"), ErrorType.VALIDATION_ERROR),
        (Exception("Anthropic API error"), ErrorType.API_ERROR),
        (Exception("Random unknown error"), ErrorType.UNKNOWN_ERROR),
    ]

    for error, expected_type in test_cases:
        classified_type = error_handler.classify_error(error)
        status = "✅" if classified_type == expected_type else "❌"
        print(f"   {status} {str(error)[:30]}... -> {classified_type.value}")

    print()


def test_retry_logic():
    """Test retry logic with mock functions."""
    print("🔄 Testing Retry Logic...")

    retry_config = RetryConfig(max_retries=2, base_delay=0.1)
    error_handler = ErrorHandler(retry_config)

    # Test successful retry
    call_count = 0

    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary failure")
        return "Success!"

    try:
        result = error_handler.retry_with_fallback(
            flaky_function, function_name="test_flaky"
        )
        print(f"   ✅ Retry successful after {call_count} attempts: {result}")
    except Exception as e:
        print(f"   ❌ Retry failed: {e}")

    # Test retry with fallback
    def always_fail():
        raise Exception("Always fails")

    def fallback_function():
        return "Fallback result"

    try:
        result = error_handler.retry_with_fallback(
            always_fail, fallback_function, function_name="test_fallback"
        )
        print(f"   ✅ Fallback successful: {result}")
    except Exception as e:
        print(f"   ❌ Fallback failed: {e}")

    print()


def test_graceful_degradation():
    """Test graceful degradation functionality."""
    print("🛡️ Testing Graceful Degradation...")

    degradation = GracefulDegradation()

    print(f"   Initial degradation level: {degradation.degradation_level}")
    print(f"   Can use tools: {degradation.should_use_tools()}")
    print(f"   Can use advanced features: {degradation.should_use_advanced_features()}")

    # Simulate errors
    for i in range(3):
        degradation.increase_degradation()
        print(f"   After error {i+1}:")
        print(f"     Level: {degradation.degradation_level}")
        print(f"     Tools: {degradation.should_use_tools()}")
        print(f"     Advanced: {degradation.should_use_advanced_features()}")

        # Test simplified responses
        response = degradation.get_simplified_response("Test user input")
        if response:
            print(f"     Simplified response: {response[:50]}...")

    # Test recovery
    for i in range(2):
        degradation.decrease_degradation()
        print(f"   After recovery {i+1}: Level {degradation.degradation_level}")

    print()


def test_agent_error_handling():
    """Test agent-level error handling."""
    print("🤖 Testing Agent Error Handling...")

    # Set up test configuration
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    config = BobConfig.from_env()

    try:
        agent = BobAgent(config)
        print("   ✅ Agent created with error handling")

        # Test degradation manager
        print(
            f"   Initial degradation level: {agent.degradation_manager.degradation_level}"
        )

        # Test retry configuration
        print(f"   Max retries: {agent.retry_config.max_retries}")
        print(f"   Base delay: {agent.retry_config.base_delay}s")

        # Test that workflow includes error handling
        print(f"   Workflow nodes: {len(agent.workflow.nodes)}")

        # Test chat with mock (won't actually call API)
        if (
            not os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY") == "test-key"
        ):
            print("   ⚠️ Using test API key - no real API calls")

    except Exception as e:
        print(f"   ❌ Agent creation failed: {e}")

    print()


def test_configuration_error_handling():
    """Test configuration-related error handling."""
    print("⚙️ Testing Configuration Error Handling...")

    # Test missing API key
    try:
        config = BobConfig(anthropic_api_key=None)
        print("   ❌ Should have failed with missing API key")
    except ValueError as e:
        print(f"   ✅ Correctly caught missing API key: {str(e)[:50]}...")

    # Test configuration from environment
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    os.environ["MAX_RETRIES"] = "5"
    os.environ["RETRY_BASE_DELAY"] = "2.0"

    try:
        config = BobConfig.from_env()
        print(f"   ✅ Configuration loaded:")
        print(f"     Max retries: {config.max_retries}")
        print(f"     Base delay: {config.retry_base_delay}")
        print(f"     Max delay: {config.retry_max_delay}")
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")

    print()


def test_real_error_simulation():
    """Test with simulated real-world errors."""
    print("🎭 Testing Simulated Real-World Errors...")

    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    config = BobConfig.from_env()
    agent = BobAgent(config)

    # Test graceful degradation under simulated stress
    print("   Simulating multiple errors...")

    for i in range(3):
        agent.degradation_manager.increase_degradation()
        user_input = f"Test message {i+1}"

        simplified = agent.degradation_manager.get_simplified_response(user_input)
        print(
            f"   Error {i+1}: {simplified[:60] if simplified else 'No simplified response'}..."
        )

    # Test recovery
    print("   Simulating recovery...")
    for i in range(2):
        agent.degradation_manager.decrease_degradation()
        print(f"   Recovery {i+1}: Level {agent.degradation_manager.degradation_level}")

    print()


def main():
    """Run all error handling tests."""
    print("🧪 Bob LangGraph Agent - Error Handling Tests")
    print("=" * 60)

    try:
        test_error_classification()
        test_retry_logic()
        test_graceful_degradation()
        test_agent_error_handling()
        test_configuration_error_handling()
        test_real_error_simulation()

        print("✅ All error handling tests completed!")

    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
