"""State management for Bob LangGraph Agent."""

from typing import List, Optional, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State for the Bob LangGraph Agent.
    
    This defines the state structure that will be passed between
    different nodes in the LangGraph workflow.
    """
    
    # Messages in the conversation
    messages: List[BaseMessage]
    
    # Current user input
    user_input: Optional[str]
    
    # Agent's response
    agent_response: Optional[str]
    
    # Iteration counter to prevent infinite loops
    iteration_count: int
    
    # Flag to indicate if the conversation should end
    should_end: bool
    
    # Any additional context or metadata
    context: Optional[dict]


def create_initial_state(user_input: str) -> AgentState:
    """Create the initial state for a new conversation.
    
    Args:
        user_input: The initial user input to start the conversation.
        
    Returns:
        AgentState: The initial state for the agent.
    """
    return AgentState(
        messages=[],
        user_input=user_input,
        agent_response=None,
        iteration_count=0,
        should_end=False,
        context={}
    )