"""Advanced workflow features for Bob LangGraph Agent."""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic

from .state import AgentState, update_metadata

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages advanced workflow features like summarization and planning."""

    def __init__(self, llm: ChatAnthropic, config):
        """Initialize the workflow manager.

        Args:
            llm: The language model instance.
            config: Agent configuration.
        """
        self.llm = llm
        self.config = config

    def summarize_conversation(self, state: AgentState) -> Dict[str, Any]:
        """Summarize the conversation history.

        Args:
            state: Current agent state.

        Returns:
            Dict with conversation summary.
        """
        try:
            messages = state.get("messages", [])
            if len(messages) < 4:  # Need at least some conversation to summarize
                return {"summary": "Conversation is too short to summarize."}

            # Prepare conversation text
            conversation_text = "\n".join(
                [
                    f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
                    for msg in messages
                    if hasattr(msg, "content")
                ]
            )

            # Create summarization prompt
            summary_messages = [
                (
                    "system",
                    "You are a helpful assistant that creates concise summaries of conversations. "
                    "Summarize the key points, decisions made, and important information discussed.",
                ),
                (
                    "human",
                    f"Please provide a concise summary of this conversation:\n\n{conversation_text}",
                ),
            ]

            # Generate summary
            response = self.llm.invoke(summary_messages)
            summary = (
                response.content if hasattr(response, "content") else str(response)
            )

            logger.info(f"Generated conversation summary: {len(summary)} characters")

            return {"summary": summary}

        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return {"summary": f"Error generating summary: {str(e)}"}

    def plan_response(self, state: AgentState) -> Dict[str, Any]:
        """Plan the agent's response strategy.

        Args:
            state: Current agent state.

        Returns:
            Dict with response plan.
        """
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                return {"plan": "No user input to plan for."}

            # Analyze the user input to create a response plan
            planning_messages = [
                (
                    "system",
                    "You are a planning assistant that helps analyze user requests and create response strategies. "
                    "Analyze the user's input and provide a brief plan for how to respond effectively.",
                ),
                (
                    "human",
                    f"Analyze this user input and create a response plan:\n\nUser: {user_input}\n\n"
                    "Consider: What is the user asking for? What type of response would be most helpful? "
                    "Are there any tools that should be used? What information is needed?",
                ),
            ]

            response = self.llm.invoke(planning_messages)
            plan = response.content if hasattr(response, "content") else str(response)

            logger.info(f"Generated response plan for user input: {user_input[:50]}...")

            return {"plan": plan}

        except Exception as e:
            logger.error(f"Error planning response: {e}")
            return {"plan": f"Error generating plan: {str(e)}"}

    def analyze_conversation_context(self, state: AgentState) -> Dict[str, Any]:
        """Analyze the conversation context for better responses.

        Args:
            state: Current agent state.

        Returns:
            Dict with context analysis.
        """
        try:
            messages = state.get("messages", [])
            metadata = state.get("metadata", {})

            # Basic analysis
            total_messages = len(messages)
            user_messages = sum(1 for msg in messages if isinstance(msg, HumanMessage))
            ai_messages = sum(1 for msg in messages if isinstance(msg, AIMessage))

            # Analyze conversation flow
            recent_topics = []
            if len(messages) >= 2:
                # Look at last few user messages for topics
                recent_user_msgs = [
                    msg.content
                    for msg in messages[-6:]
                    if isinstance(msg, HumanMessage) and hasattr(msg, "content")
                ]
                recent_topics = recent_user_msgs

            # Determine conversation stage
            if total_messages == 0:
                stage = "beginning"
            elif total_messages < 6:
                stage = "early"
            elif total_messages < 15:
                stage = "middle"
            else:
                stage = "extended"

            context_analysis = {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "ai_messages": ai_messages,
                "conversation_stage": stage,
                "recent_topics": recent_topics,
                "conversation_length_minutes": self._estimate_conversation_duration(
                    metadata
                ),
                "needs_summary": total_messages > 20,
            }

            logger.info(
                f"Context analysis: {stage} stage conversation with {total_messages} messages"
            )

            return {"context_analysis": context_analysis}

        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return {"context_analysis": {"error": str(e)}}

    def _estimate_conversation_duration(self, metadata: dict) -> Optional[float]:
        """Estimate conversation duration in minutes.

        Args:
            metadata: Conversation metadata.

        Returns:
            Duration in minutes or None if cannot calculate.
        """
        try:
            if not metadata.get("start_time") or not metadata.get("last_updated"):
                return None

            from datetime import datetime

            start = datetime.fromisoformat(metadata["start_time"])
            end = datetime.fromisoformat(metadata["last_updated"])
            duration = (end - start).total_seconds() / 60

            return round(duration, 1)
        except Exception:
            return None


def create_advanced_workflow_node(workflow_manager: WorkflowManager):
    """Create a workflow node for advanced features.

    Args:
        workflow_manager: The workflow manager instance.

    Returns:
        Function that can be used as a workflow node.
    """

    def advanced_processing(state: AgentState) -> Dict[str, Any]:
        """Process advanced workflow features.

        Args:
            state: Current agent state.

        Returns:
            Dict with updated state.
        """
        try:
            # Analyze context
            context_result = workflow_manager.analyze_conversation_context(state)
            context_analysis = context_result.get("context_analysis", {})

            # Add context to state
            current_context = state.get("context", {})
            current_context.update(
                {
                    "workflow_analysis": context_analysis,
                    "last_analysis_update": update_metadata(state)
                    .get("metadata", {})
                    .get("last_updated"),
                }
            )

            # Check if summarization is needed
            if context_analysis.get("needs_summary", False):
                summary_result = workflow_manager.summarize_conversation(state)
                current_context["conversation_summary"] = summary_result.get("summary")

            # Plan response if there's user input
            if state.get("user_input"):
                plan_result = workflow_manager.plan_response(state)
                current_context["response_plan"] = plan_result.get("plan")

            logger.info("Advanced workflow processing completed")

            return {"context": current_context}

        except Exception as e:
            logger.error(f"Error in advanced workflow processing: {e}")
            return {"context": state.get("context", {})}

    return advanced_processing
