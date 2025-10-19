"""Configuration for Bob LangGraph Agent."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class BobConfig:
    """Configuration for Bob LangGraph Agent.
    
    This class handles the configuration settings for the agent,
    including API keys and model settings.
    """
    
    # Anthropic API settings
    anthropic_api_key: Optional[str] = None
    model_name: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Agent settings
    agent_name: str = "Bob"
    system_message: str = "You are Bob, a helpful AI assistant and operations buddy."
    max_iterations: int = 10
    
    def __post_init__(self):
        """Post-initialization to set API key from environment if not provided."""
        if self.anthropic_api_key is None:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be provided either as a parameter "
                "or as an environment variable"
            )
    
    @classmethod
    def from_env(cls) -> "BobConfig":
        """Create configuration from environment variables."""
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            model_name=os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-5-sonnet-20241022"),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
            agent_name=os.getenv("AGENT_NAME", "Bob"),
            system_message=os.getenv("SYSTEM_MESSAGE", "You are Bob, a helpful AI assistant and operations buddy."),
            max_iterations=int(os.getenv("MAX_ITERATIONS", "10")),
        )