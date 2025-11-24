"""Bob LangGraph Agent implementation."""

import logging
from typing import Any, Dict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

from config import BobConfig
from state import (
    AgentState,
    create_initial_state,
    validate_state,
    update_metadata,
    truncate_conversation_history,
    handle_state_error,
    reset_error_state,
)
from tools import get_tools
from workflow import WorkflowManager, create_advanced_workflow_node
from error_handling import (
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
        # Only do advanced processing if we have user input
        workflow.add_conditional_edges(
            "process_input",
            lambda state: "advanced" if state.get("user_input") else "generate",
            {
                "advanced": "advanced_processing",
                "generate": "generate_response",
            },
        )
        workflow.add_edge("advanced_processing", "generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            self._should_use_tools,
            {
                "tools": "tools",
                "continue": "update_state",
            },
        )
        # After tools execute, generate a final response with the tool results
        workflow.add_edge("tools", "generate_response")
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
            if state.get("user_input"):
                # Add user message to the conversation
                human_message = HumanMessage(content=state["user_input"])
                messages = state["messages"] + [human_message]

                updated_state = {
                    "messages": messages,
                    "iteration_count": state["iteration_count"] + 1,
                    "user_input": None,  # Clear user input after processing
                }

                # Update metadata
                new_state = {**state, **updated_state}
                new_state = update_metadata(new_state)
                new_state = truncate_conversation_history(
                    new_state, max_messages=self.config.max_conversation_history
                )
                new_state = reset_error_state(new_state)

                logger.debug(
                    f"_process_input: Processed user input, cleared it, messages count={len(new_state['messages'])}"
                )
                return new_state

            # No user input to process, just increment iteration
            logger.debug(f"_process_input: No user input, skipping processing")
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
            logger.debug(f"State messages count: {len(state['messages'])}")
            for i, msg in enumerate(state["messages"]):
                logger.debug(
                    f"Processing message {i}: type={type(msg)}, hasattr tool_calls={hasattr(msg, 'tool_calls') if isinstance(msg, AIMessage) else 'N/A'}"
                )
                if isinstance(msg, HumanMessage):
                    messages.append(("human", msg.content))
                elif isinstance(msg, AIMessage):
                    # For AIMessages, include both content and tool_calls
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        # This is an AIMessage requesting tool calls - include it properly
                        messages.append(msg)
                        logger.debug(
                            f"Added AIMessage with {len(msg.tool_calls)} tool_calls"
                        )
                    else:
                        messages.append(("assistant", msg.content))
                elif isinstance(msg, ToolMessage):
                    # Include tool results in the conversation
                    messages.append(msg)
                    logger.debug(f"Added ToolMessage: {msg.content[:50]}")

            logger.debug(f"Generating response with {len(messages)} messages")
            logger.debug(f"Message types: {[type(m) for m in messages]}")

            # Generate response
            response = self.llm.invoke(messages)

            logger.debug(
                f"Generated response type: {type(response)}, has content: {hasattr(response, 'content')}"
            )
            if hasattr(response, "content"):
                logger.debug(
                    f"Response content: {response.content[:100] if response.content else 'None'}"
                )

            # Only return the fields we want to update, not the entire state
            result_dict = {
                "agent_response": response,
                "last_error": None,
                "retry_count": 0,
            }

            # If the response has tool_calls, add it to messages immediately
            # so the ToolNode can access it
            if hasattr(response, "tool_calls") and response.tool_calls:
                result_dict["messages"] = state["messages"] + [response]
                logger.debug(
                    f"Added AIMessage with {len(response.tool_calls)} tool_calls to messages list"
                )

            logger.debug(
                f"_generate_response returning: agent_response={type(response)}, content={response.content[:50] if hasattr(response, 'content') and response.content else 'None'}"
            )
            return result_dict

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
            logger.debug(
                f"_update_state: agent_response type={type(agent_response)}, value={repr(agent_response)[:100]}"
            )
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
            logger.debug(
                f"_should_continue: END - should_end={state['should_end']}, iterations={state['iteration_count']}"
            )
            return END_CONVERSATION

        # For single-turn conversations, end after the first iteration if no user input remains
        if not state.get("continue_conversation", False):
            # If we've processed at least one iteration and there's no more user input, end
            if state["iteration_count"] >= 1 and not state.get("user_input"):
                logger.debug(
                    "_should_continue: END - single turn complete (no more user input)"
                )
                return END_CONVERSATION

        logger.debug(
            f"_should_continue: CONTINUE - continue_conversation={state.get('continue_conversation')}, iter={state['iteration_count']}"
        )
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

            logger.debug(f"Workflow result keys: {result.keys()}")
            logger.debug(f"Messages in result: {len(result.get('messages', []))}")

            # Extract the final response from the last AI message in the conversation
            messages = result.get("messages", [])
            if messages:
                # Get the last AI message that has actual content (not just tool calls)
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage):
                        # Check if this message has actual content (not just tool calls)
                        if (
                            msg.content
                            and isinstance(msg.content, str)
                            and msg.content.strip()
                        ):
                            logger.debug(
                                f"Found last AI message with content: {msg.content[:100]}"
                            )
                            return msg.content
                        # If no content but has tool_calls, this is a tool request - keep looking
                        elif hasattr(msg, "tool_calls") and msg.tool_calls:
                            logger.debug(
                                "Skipping AIMessage with tool_calls, looking for final response"
                            )
                            continue
                        # If content is empty, try the next message
                        else:
                            logger.debug(
                                f"Found AI message but content is: {repr(msg.content)}"
                            )

            # Fallback: try agent_response field
            agent_response = result.get("agent_response", "")
            if agent_response:
                if hasattr(agent_response, "content") and agent_response.content:
                    return agent_response.content
                return str(agent_response)

            return "No response generated."

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
