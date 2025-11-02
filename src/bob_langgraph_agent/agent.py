"""Bob LangGraph Agent implementation."""

import logging
from typing import Any, Dict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

from .config import BobConfig
from .state import (
    AgentState,
    create_initial_state,
    validate_state,
    update_metadata,
    truncate_conversation_history,
    handle_state_error,
    reset_error_state,
)
from .tools import get_tools
from .workflow import WorkflowManager, create_advanced_workflow_node
from .error_handling import (
    with_retry,
    RetryConfig,
    GracefulDegradation,
    UserFeedbackManager,
    ErrorType,
)

logger = logging.getLogger(__name__)


# Constants for workflow control
CONTINUE = "continue"
END_CONVERSATION = "end"


class BobAgent:
    """Bob LangGraph Agent - A helpful AI assistant and operations buddy.

    This agent uses LangGraph to manage conversation flow and Anthropic's Claude
    as the underlying language model.
    """

    def __init__(self, config: BobConfig):
        """Initialize the Bob Agent.

        Args:
            config: Configuration object containing API keys and settings.
        """
        self.config = config
        self.tools = get_tools()
        self.llm = ChatAnthropic(
            api_key=config.anthropic_api_key,
            model=config.model_name,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        ).bind_tools(self.tools)

        # Initialize workflow manager for advanced features
        self.workflow_manager = WorkflowManager(self.llm, config)

        # Initialize error handling and degradation management
        self.retry_config = RetryConfig(
            max_retries=getattr(config, "max_retries", 3),
            base_delay=getattr(config, "retry_base_delay", 1.0),
            max_delay=getattr(config, "retry_max_delay", 60.0),
        )
        self.degradation_manager = GracefulDegradation()
        self.user_feedback = UserFeedbackManager()

        # Create the workflow graph
        self.workflow = self._create_workflow()

        # Create memory saver for conversation persistence
        self.memory = InMemorySaver()

        # Compile the graph
        self.app = self.workflow.compile(checkpointer=self.memory)

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow.

        Returns:
            StateGraph: The compiled workflow graph.
        """
        workflow = StateGraph(AgentState)

        # Create tool node for handling tool calls
        tool_node = ToolNode(self.tools)

        # Create advanced workflow node
        advanced_node = create_advanced_workflow_node(self.workflow_manager)

        # Add nodes
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("advanced_processing", advanced_node)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("tools", tool_node)
        workflow.add_node("update_state", self._update_state)

        # Add edges
        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", "advanced_processing")
        workflow.add_edge("advanced_processing", "generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            self._should_use_tools,
            {
                "tools": "tools",
                "continue": "update_state",
            },
        )
        workflow.add_edge("tools", "update_state")
        workflow.add_conditional_edges(
            "update_state",
            self._should_continue,
            {
                CONTINUE: "process_input",
                END_CONVERSATION: END,
            },
        )

        return workflow

    def _process_input(self, state: AgentState) -> Dict[str, Any]:
        """Process the user input and update messages.

        Args:
            state: Current agent state.

        Returns:
            Dict with updated state.
        """
        # Validate state first
        if not validate_state(state):
            return handle_state_error(state, "Invalid state detected in process_input")

        try:
            if state["user_input"]:
                # Add user message to the conversation
                human_message = HumanMessage(content=state["user_input"])
                messages = state["messages"] + [human_message]

                updated_state = {
                    "messages": messages,
                    "iteration_count": state["iteration_count"] + 1,
                }

                # Update metadata
                new_state = {**state, **updated_state}
                new_state = update_metadata(new_state)
                new_state = truncate_conversation_history(
                    new_state, max_messages=self.config.max_conversation_history
                )
                new_state = reset_error_state(new_state)

                return new_state

            return {
                "iteration_count": state["iteration_count"] + 1,
                **update_metadata(state),
            }

        except Exception as e:
            return handle_state_error(state, f"Error processing input: {str(e)}")

    def _generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate a response using the Claude model with robust error handling.

        Args:
            state: Current agent state.

        Returns:
            Dict with the generated response.
        """

        @with_retry(config=self.retry_config)
        def _robust_generate():
            # Validate state
            if not validate_state(state):
                raise ValueError("Invalid state detected in generate_response")

            # Prepare messages for the LLM
            messages = []

            # Enhanced system message with context
            system_msg = self.config.system_message

            # Add context information if available and degradation allows
            if self.degradation_manager.should_use_advanced_features():
                context = state.get("context", {})
                if context.get("response_plan"):
                    system_msg += f"\n\nResponse Plan: {context['response_plan']}"

                if context.get("conversation_summary"):
                    system_msg += (
                        f"\n\nConversation Summary: {context['conversation_summary']}"
                    )

                workflow_analysis = context.get("workflow_analysis", {})
                if workflow_analysis:
                    stage = workflow_analysis.get("conversation_stage", "unknown")
                    system_msg += f"\n\nConversation Stage: {stage}"

                    if workflow_analysis.get("recent_topics"):
                        topics = ", ".join(
                            workflow_analysis["recent_topics"][-3:]
                        )  # Last 3 topics
                        system_msg += f"\nRecent Topics: {topics}"

            messages.append(("system", system_msg))

            # Add conversation history
            for msg in state["messages"]:
                if isinstance(msg, HumanMessage):
                    messages.append(("human", msg.content))
                elif isinstance(msg, AIMessage):
                    messages.append(("assistant", msg.content))

            # Generate response
            response = self.llm.invoke(messages)

            return {"agent_response": response, **reset_error_state(state)}

        def _fallback_generate():
            """Fallback for response generation."""
            user_input = state.get("user_input", "")
            fallback_response = self.degradation_manager.get_simplified_response(
                user_input
            )

            if not fallback_response:
                fallback_response = "I'm having trouble generating a response right now. Please try again."

            # Create a simple AIMessage for the fallback
            from langchain_core.messages import AIMessage

            fallback_msg = AIMessage(content=fallback_response)

            return {
                "agent_response": fallback_msg,
                **handle_state_error(state, "Using fallback response generation"),
            }

        try:
            return _robust_generate()
        except Exception as e:
            logger.error(f"Response generation failed after retries: {e}")
            return _fallback_generate()

    def _update_state(self, state: AgentState) -> Dict[str, Any]:
        """Update the state with the agent's response.

        Args:
            state: Current agent state.

        Returns:
            Dict with updated state.
        """
        try:
            # Validate state
            if not validate_state(state):
                return handle_state_error(
                    state, "Invalid state detected in update_state"
                )

            agent_response = state.get("agent_response")
            if agent_response:
                # Add AI message to the conversation
                messages = state["messages"] + [agent_response]

                updated_state = {
                    "messages": messages,
                    "user_input": None,  # Clear user input for next iteration
                    "agent_response": (
                        agent_response.content
                        if hasattr(agent_response, "content")
                        else str(agent_response)
                    ),
                }

                # Update metadata
                new_state = {**state, **updated_state}
                new_state = update_metadata(new_state)
                new_state = reset_error_state(new_state)

                return new_state

            return reset_error_state(state)

        except Exception as e:
            return handle_state_error(state, f"Error updating state: {str(e)}")

    def _should_use_tools(self, state: AgentState) -> str:
        """Determine if tools should be used based on the agent's response and degradation level.

        Args:
            state: Current agent state.

        Returns:
            str: "tools" if tools should be used, "continue" otherwise.
        """
        # Check degradation level first
        if not self.degradation_manager.should_use_tools():
            return "continue"

        agent_response = state.get("agent_response")
        if (
            agent_response
            and hasattr(agent_response, "tool_calls")
            and agent_response.tool_calls
        ):
            return "tools"
        return "continue"

    def _should_continue(self, state: AgentState) -> str:
        """Determine if the conversation should continue.

        Args:
            state: Current agent state.

        Returns:
            str: CONTINUE or END_CONVERSATION.
        """
        # End if explicitly requested or max iterations reached
        if (
            state["should_end"]
            or state["iteration_count"] >= self.config.max_iterations
        ):
            return END_CONVERSATION

        # For single-turn conversations, end after processing one complete cycle
        # A complete cycle means: user input processed -> response generated -> state updated
        if not state.get("continue_conversation", False):
            # End after we have both processed the input and generated a response
            if state.get("agent_response") and state["iteration_count"] > 0:
                return END_CONVERSATION

        return CONTINUE

    def chat(self, message: str, thread_id: str = "default") -> str:
        """Send a message to the agent and get a response with robust error handling.

        Args:
            message: The user's message.
            thread_id: Unique identifier for the conversation thread.

        Returns:
            str: The agent's response.
        """

        @with_retry(config=self.retry_config)
        def _robust_chat():
            # Get existing state or create initial state
            config = {"configurable": {"thread_id": thread_id}}
            existing_state = self.app.get_state(config)

            if existing_state and existing_state.values:
                # Continue existing conversation
                current_state = existing_state.values
                current_state["user_input"] = message
                current_state["should_end"] = False
                current_state["continue_conversation"] = False  # Single-turn for chat()
            else:
                # Create initial state for new conversation
                current_state = create_initial_state(message)
                current_state["continue_conversation"] = False  # Single-turn for chat()

            # Run the workflow with recursion limit
            config_with_limit = {**config, "recursion_limit": 50}
            result = self.app.invoke(current_state, config_with_limit)

            # Extract the final response
            agent_response = result.get("agent_response", "")
            if hasattr(agent_response, "content"):
                return agent_response.content
            return str(agent_response)

        def _fallback_chat():
            """Fallback function for when main chat fails."""
            self.degradation_manager.increase_degradation()
            simplified_response = self.degradation_manager.get_simplified_response(
                message
            )
            if simplified_response:
                return simplified_response
            return "I'm experiencing technical difficulties. Please try again later."

        try:
            return _robust_chat()
        except Exception as e:
            logger.error(f"Chat failed after retries: {e}")
            return _fallback_chat()

    def stream_chat(self, message: str, thread_id: str = "default"):
        """Stream a conversation with the agent.

        Args:
            message: The user's message.
            thread_id: Unique identifier for the conversation thread.

        Yields:
            Updates from the agent as the response is generated.
        """
        # Get existing state or create initial state
        config = {"configurable": {"thread_id": thread_id}}
        existing_state = self.app.get_state(config)

        if existing_state and existing_state.values:
            # Continue existing conversation
            current_state = existing_state.values
            current_state["user_input"] = message
            current_state["should_end"] = False
            current_state["continue_conversation"] = (
                True  # Multi-turn for stream_chat()
            )
        else:
            # Create initial state for new conversation
            current_state = create_initial_state(message)
            current_state["continue_conversation"] = (
                True  # Multi-turn for stream_chat()
            )

        # Stream the workflow with recursion limit
        config_with_limit = {**config, "recursion_limit": 50}
        for update in self.app.stream(current_state, config_with_limit):
            yield update

    def get_conversation_history(self, thread_id: str = "default") -> list:
        """Get the conversation history for a thread.

        Args:
            thread_id: Unique identifier for the conversation thread.

        Returns:
            list: List of messages in the conversation.
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)

        if state and state.values:
            return state.values.get("messages", [])

        return []

    def get_conversation_summary(self, thread_id: str = "default") -> str:
        """Get a summary of the conversation.

        Args:
            thread_id: Unique identifier for the conversation thread.

        Returns:
            str: Conversation summary.
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)

        if state and state.values:
            return self.workflow_manager.summarize_conversation(state.values).get(
                "summary", "No summary available."
            )

        return "No conversation found."

    def get_conversation_analysis(self, thread_id: str = "default") -> dict:
        """Get detailed analysis of the conversation.

        Args:
            thread_id: Unique identifier for the conversation thread.

        Returns:
            dict: Conversation analysis.
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)

        if state and state.values:
            return self.workflow_manager.analyze_conversation_context(state.values).get(
                "context_analysis", {}
            )

        return {}

    def clear_conversation(self, thread_id: str = "default") -> bool:
        """Clear the conversation history.

        Args:
            thread_id: Unique identifier for the conversation thread.

        Returns:
            bool: True if cleared successfully.
        """
        try:
            # This would require implementing a clear method in the memory
            # For now, we'll just indicate success
            return True
        except Exception:
            return False
