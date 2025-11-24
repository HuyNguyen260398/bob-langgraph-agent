"""
Quick test script for the Bob LangGraph Agent API.

This script tests the deployed API endpoints to ensure the agent is working correctly.
"""

import requests
import time
import sys
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_THREAD_ID = "test-session"


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text: str):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message."""
    print(f"❌ {text}")


def print_info(text: str):
    """Print info message."""
    print(f"ℹ️  {text}")


def test_health_check() -> bool:
    """Test the health check endpoint."""
    print_header("Testing Health Check")

    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()

        data = response.json()
        print_success(f"Health check passed - Status: {data['status']}")
        print_info(f"Model: {data.get('model', 'unknown')}")
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_root_endpoint() -> bool:
    """Test the root endpoint."""
    print_header("Testing Root Endpoint")

    try:
        response = requests.get(f"{API_BASE_URL}/")
        response.raise_for_status()

        data = response.json()
        print_success(f"Root endpoint accessible - {data['name']}")
        print_info(f"Version: {data.get('version', 'unknown')}")
        return True
    except Exception as e:
        print_error(f"Root endpoint test failed: {e}")
        return False


def test_chat(message: str) -> Dict[str, Any]:
    """Test the chat endpoint."""
    print_header(f"Testing Chat: '{message}'")

    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": message, "thread_id": TEST_THREAD_ID},
        )
        response.raise_for_status()

        data = response.json()
        print_success("Chat request successful")
        print_info(f"Thread ID: {data['thread_id']}")
        print(f"\n📝 Agent Response:\n{data['response']}\n")
        return data
    except Exception as e:
        print_error(f"Chat test failed: {e}")
        return {}


def test_history() -> bool:
    """Test the conversation history endpoint."""
    print_header("Testing Conversation History")

    try:
        response = requests.get(f"{API_BASE_URL}/history/{TEST_THREAD_ID}")
        response.raise_for_status()

        data = response.json()
        print_success(f"History retrieved - {data['message_count']} messages")

        for i, msg in enumerate(data["messages"][-3:], 1):  # Show last 3 messages
            print(f"  {i}. [{msg['type']}]: {msg['content'][:60]}...")

        return True
    except Exception as e:
        print_error(f"History test failed: {e}")
        return False


def test_summary() -> bool:
    """Test the conversation summary endpoint."""
    print_header("Testing Conversation Summary")

    try:
        response = requests.get(f"{API_BASE_URL}/summary/{TEST_THREAD_ID}")
        response.raise_for_status()

        data = response.json()
        print_success("Summary generated")
        print(f"\n📊 Summary:\n{data['summary']}\n")
        return True
    except Exception as e:
        print_error(f"Summary test failed: {e}")
        return False


def test_analysis() -> bool:
    """Test the conversation analysis endpoint."""
    print_header("Testing Conversation Analysis")

    try:
        response = requests.get(f"{API_BASE_URL}/analysis/{TEST_THREAD_ID}")
        response.raise_for_status()

        data = response.json()
        analysis = data["analysis"]

        print_success("Analysis generated")
        print(f"  • Total Messages: {analysis.get('total_messages', 0)}")
        print(f"  • User Messages: {analysis.get('user_messages', 0)}")
        print(f"  • Agent Messages: {analysis.get('agent_messages', 0)}")
        print(f"  • Tools Used: {analysis.get('tool_calls', 0)}")

        return True
    except Exception as e:
        print_error(f"Analysis test failed: {e}")
        return False


def test_clear_thread() -> bool:
    """Test clearing the conversation thread."""
    print_header("Testing Thread Cleanup")

    try:
        response = requests.delete(f"{API_BASE_URL}/thread/{TEST_THREAD_ID}")
        response.raise_for_status()

        data = response.json()
        print_success(f"Thread cleared - {data['thread_id']}")
        return True
    except Exception as e:
        print_error(f"Thread cleanup test failed: {e}")
        return False


def run_all_tests():
    """Run all API tests."""
    print("\n" + "🧪 " * 20)
    print("Starting Bob LangGraph Agent API Tests")
    print("🧪 " * 20)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Health Check
    if test_health_check():
        tests_passed += 1
    else:
        tests_failed += 1
        print_error("Aborting tests - API not healthy")
        return False

    time.sleep(1)

    # Test 2: Root Endpoint
    if test_root_endpoint():
        tests_passed += 1
    else:
        tests_failed += 1

    time.sleep(1)

    # Test 3: Basic Chat
    if test_chat("Hello! What's your name?"):
        tests_passed += 1
    else:
        tests_failed += 1

    time.sleep(2)

    # Test 4: Follow-up Chat
    if test_chat("What can you help me with?"):
        tests_passed += 1
    else:
        tests_failed += 1

    time.sleep(2)

    # Test 5: Conversation History
    if test_history():
        tests_passed += 1
    else:
        tests_failed += 1

    time.sleep(1)

    # Test 6: Conversation Summary
    if test_summary():
        tests_passed += 1
    else:
        tests_failed += 1

    time.sleep(1)

    # Test 7: Conversation Analysis
    if test_analysis():
        tests_passed += 1
    else:
        tests_failed += 1

    time.sleep(1)

    # Test 8: Clear Thread
    if test_clear_thread():
        tests_passed += 1
    else:
        tests_failed += 1

    # Summary
    print_header("Test Summary")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"📊 Total: {tests_passed + tests_failed}")

    if tests_failed == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed")
        return False


if __name__ == "__main__":
    print_info(f"Testing API at: {API_BASE_URL}")
    print_info("Make sure the agent is running: docker-compose up -d")
    print_info("Waiting 2 seconds before starting tests...\n")

    time.sleep(2)

    success = run_all_tests()

    sys.exit(0 if success else 1)
