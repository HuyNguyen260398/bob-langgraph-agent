"""State management for Bob LangGraph Agent."""

from typing import List, Optional, TypedDict, Union, Dict, Any, Annotated
from datetime import datetime
import logging
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages

# Set up logging
logger = logging.getLogger(__name__)


class ConversationMetadata(TypedDict):
    """Metadata for conversation tracking."""

    start_time: str
    last_updated: str
    total_messages: int
    total_tokens_estimate: int
    conversation_id: str
    user_preferences: Dict[str, Any]


class AgentState(TypedDict):
    """State for the Bob LangGraph Agent.

    This defines the state structure that will be passed between
    different nodes in the LangGraph workflow.
    """

    # Messages in the conversation - uses add_messages reducer to append instead of replace
    messages: Annotated[List[BaseMessage], add_messages]

    # Current user input
    user_input: Optional[str]

    # Agent's response (can be a message object or string)
    agent_response: Optional[Union[BaseMessage, str]]

    # Iteration counter to prevent infinite loops
    iteration_count: int

    # Flag to indicate if the conversation should end
    should_end: bool

    # Flag to indicate if this is a multi-turn conversation
    continue_conversation: bool

    # Enhanced metadata and context
    context: Optional[Dict[str, Any]]
    metadata: Optional[ConversationMetadata]

    # Error handling
    last_error: Optional[str]
    retry_count: int


def create_initial_state(user_input: str, conversation_id: str = None) -> AgentState:
    """Create the initial state for a new conversation.

    Args:
        user_input: The initial user input to start the conversation.
        conversation_id: Optional conversation identifier.

    Returns:
        AgentState: The initial state for the agent.
    """
    if conversation_id is None:
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    current_time = datetime.now().isoformat()

    metadata: ConversationMetadata = {
        "start_time": current_time,
        "last_updated": current_time,
        "total_messages": 0,
        "total_tokens_estimate": 0,
        "conversation_id": conversation_id,
        "user_preferences": {},
    }

    return AgentState(
        messages=[],
        user_input=user_input,
        agent_response=None,
        iteration_count=0,
        should_end=False,
        continue_conversation=False,  # Default to single-turn
        context={},
        metadata=metadata,
        last_error=None,
        retry_count=0,
    )


def validate_state(state: AgentState) -> bool:
    """Validate the agent state.

    Args:
        state: The state to validate.

    Returns:
        bool: True if state is valid, False otherwise.
    """
    try:
        # Check required fields
        if not isinstance(state.get("messages", []), list):
            logger.error("Messages field must be a list")
            return False

        if not isinstance(state.get("iteration_count", 0), int):
            logger.error("iteration_count must be an integer")
            return False

        if state.get("iteration_count", 0) < 0:
            logger.error("iteration_count cannot be negative")
            return False

        # Validate messages
        for i, msg in enumerate(state.get("messages", [])):
            if not isinstance(msg, BaseMessage):
                logger.error(f"Message {i} is not a BaseMessage instance")
                return False

        # Check metadata structure if present
        metadata = state.get("metadata")
        if metadata:
            required_fields = ["start_time", "last_updated", "conversation_id"]
            for field in required_fields:
                if field not in metadata:
                    logger.error(f"Missing required metadata field: {field}")
                    return False

        return True

    except Exception as e:
        logger.error(f"Error validating state: {e}")
        return False


def update_metadata(state: AgentState) -> AgentState:
    """Update metadata in the state.

    Args:
        state: Current state.

    Returns:
        AgentState: Updated state with current metadata.
    """
    if not state.get("metadata"):
        # Initialize metadata if not present
        state["metadata"] = ConversationMetadata(
            start_time=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            total_messages=len(state.get("messages", [])),
            total_tokens_estimate=0,
            conversation_id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_preferences={},
        )
    else:
        # Update existing metadata
        state["metadata"]["last_updated"] = datetime.now().isoformat()
        state["metadata"]["total_messages"] = len(state.get("messages", []))

        # Estimate tokens (rough approximation: 4 chars = 1 token)
        total_chars = sum(
            len(msg.content) if hasattr(msg, "content") else 0
            for msg in state.get("messages", [])
        )
        state["metadata"]["total_tokens_estimate"] = total_chars // 4

    return state


def truncate_conversation_history(
    state: AgentState, max_messages: int = 20
) -> AgentState:
    """Truncate conversation history to manage memory.

    Args:
        state: Current state.
        max_messages: Maximum number of messages to keep.

    Returns:
        AgentState: State with truncated message history.
    """
    messages = state.get("messages", [])

    if len(messages) > max_messages:
        # Keep the first message (often system) and recent messages
        if len(messages) > 1:
            truncated = [messages[0]] + messages[-(max_messages - 1) :]
        else:
            truncated = messages[-max_messages:]

        state["messages"] = truncated

        logger.info(
            f"Truncated conversation history from {len(messages)} to {len(truncated)} messages"
        )

        # Update context to note truncation
        if not state.get("context"):
            state["context"] = {}
        state["context"]["truncated"] = True
        state["context"]["original_message_count"] = len(messages)

    return state


def handle_state_error(state: AgentState, error: str) -> AgentState:
    """Handle and log state errors.

    Args:
        state: Current state.
        error: Error message.

    Returns:
        AgentState: State updated with error information.
    """
    logger.error(f"State error: {error}")

    state["last_error"] = error
    state["retry_count"] = state.get("retry_count", 0) + 1

    # Update metadata if present
    if state.get("metadata"):
        state["metadata"]["last_updated"] = datetime.now().isoformat()

    return state


def reset_error_state(state: AgentState) -> AgentState:
    """Reset error information in state.

    Args:
        state: Current state.

    Returns:
        AgentState: State with cleared error information.
    """
    state["last_error"] = None
    state["retry_count"] = 0
    return state
