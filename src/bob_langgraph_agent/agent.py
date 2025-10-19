"""Bob LangGraph Agent implementation."""

from typing import Any, Dict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .config import BobConfig
from .state import AgentState, create_initial_state


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
        self.llm = ChatAnthropic(
            api_key=config.anthropic_api_key,
            model=config.model_name,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        
        # Create memory saver for conversation persistence
        self.memory = MemorySaver()
        
        # Compile the graph
        self.app = self.workflow.compile(checkpointer=self.memory)
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow.
        
        Returns:
            StateGraph: The compiled workflow graph.
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("update_state", self._update_state)
        
        # Add edges
        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", "generate_response")
        workflow.add_edge("generate_response", "update_state")
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
        if state["user_input"]:
            # Add user message to the conversation
            human_message = HumanMessage(content=state["user_input"])
            messages = state["messages"] + [human_message]
            
            return {
                "messages": messages,
                "iteration_count": state["iteration_count"] + 1,
            }
        
        return {"iteration_count": state["iteration_count"] + 1}
    
    def _generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate a response using the Claude model.
        
        Args:
            state: Current agent state.
            
        Returns:
            Dict with the generated response.
        """
        # Prepare messages for the LLM
        messages = []
        
        # Add system message
        if self.config.system_message:
            messages.append(("system", self.config.system_message))
        
        # Add conversation history
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                messages.append(("human", msg.content))
            elif isinstance(msg, AIMessage):
                messages.append(("assistant", msg.content))
        
        # Generate response
        response = self.llm.invoke(messages)
        
        return {
            "agent_response": response.content,
        }
    
    def _update_state(self, state: AgentState) -> Dict[str, Any]:
        """Update the state with the agent's response.
        
        Args:
            state: Current agent state.
            
        Returns:
            Dict with updated state.
        """
        if state["agent_response"]:
            # Add AI message to the conversation
            ai_message = AIMessage(content=state["agent_response"])
            messages = state["messages"] + [ai_message]
            
            return {
                "messages": messages,
                "user_input": None,  # Clear user input for next iteration
            }
        
        return {}
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if the conversation should continue.
        
        Args:
            state: Current agent state.
            
        Returns:
            str: CONTINUE or END_CONVERSATION.
        """
        # End if explicitly requested or max iterations reached
        if state["should_end"] or state["iteration_count"] >= self.config.max_iterations:
            return END_CONVERSATION
        
        return CONTINUE
    
    def chat(self, message: str, thread_id: str = "default") -> str:
        """Send a message to the agent and get a response.
        
        Args:
            message: The user's message.
            thread_id: Unique identifier for the conversation thread.
            
        Returns:
            str: The agent's response.
        """
        # Get existing state or create initial state
        config = {"configurable": {"thread_id": thread_id}}
        existing_state = self.app.get_state(config)
        
        if existing_state and existing_state.values:
            # Continue existing conversation
            current_state = existing_state.values
            current_state["user_input"] = message
            current_state["should_end"] = False
        else:
            # Create initial state for new conversation
            current_state = create_initial_state(message)
        
        # Run the workflow
        result = self.app.invoke(current_state, config)
        
        return result["agent_response"]
    
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
        else:
            # Create initial state for new conversation
            current_state = create_initial_state(message)
        
        # Stream the workflow
        for update in self.app.stream(current_state, config):
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