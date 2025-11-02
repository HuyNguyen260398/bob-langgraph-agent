"""Enhanced error handling and retry logic for Bob LangGraph Agent."""

import logging
import time
import random
from typing import Any, Dict, Optional, Callable, List
from functools import wraps
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur."""

    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_errors: List[ErrorType] = None

    def __post_init__(self):
        if self.retry_on_errors is None:
            self.retry_on_errors = [
                ErrorType.API_ERROR,
                ErrorType.RATE_LIMIT,
                ErrorType.NETWORK_ERROR,
                ErrorType.TIMEOUT_ERROR,
            ]


class ErrorHandler:
    """Centralized error handling with retry logic."""

    def __init__(self, config: RetryConfig = None):
        """Initialize error handler.

        Args:
            config: Retry configuration.
        """
        self.config = config or RetryConfig()
        self.error_history: List[Dict[str, Any]] = []

    def classify_error(self, error: Exception) -> ErrorType:
        """Classify the type of error.

        Args:
            error: The exception to classify.

        Returns:
            ErrorType: The classified error type.
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # API-related errors
        if "api" in error_str or "anthropic" in error_str:
            return ErrorType.API_ERROR

        # Rate limiting
        if "rate" in error_str or "limit" in error_str or "429" in error_str:
            return ErrorType.RATE_LIMIT

        # Network errors
        if any(
            term in error_str
            for term in ["connection", "network", "timeout", "unreachable"]
        ):
            return ErrorType.NETWORK_ERROR

        # Timeout errors
        if "timeout" in error_str or "timeouterror" in error_type:
            return ErrorType.TIMEOUT_ERROR

        # Validation errors
        if any(term in error_type for term in ["value", "type", "attribute", "key"]):
            return ErrorType.VALIDATION_ERROR

        return ErrorType.UNKNOWN_ERROR

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if an error should trigger a retry.

        Args:
            error: The exception that occurred.
            attempt: Current attempt number (0-indexed).

        Returns:
            bool: True if should retry, False otherwise.
        """
        if attempt >= self.config.max_retries:
            return False

        error_type = self.classify_error(error)
        return error_type in self.config.retry_on_errors

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the next retry.

        Args:
            attempt: Current attempt number (0-indexed).

        Returns:
            float: Delay in seconds.
        """
        delay = self.config.base_delay * (self.config.exponential_base**attempt)
        delay = min(delay, self.config.max_delay)

        if self.config.jitter:
            delay += random.uniform(0, delay * 0.1)  # Add up to 10% jitter

        return delay

    def log_error(self, error: Exception, attempt: int, function_name: str):
        """Log error information.

        Args:
            error: The exception that occurred.
            attempt: Current attempt number.
            function_name: Name of the function where error occurred.
        """
        error_type = self.classify_error(error)

        error_info = {
            "timestamp": time.time(),
            "function": function_name,
            "error_type": error_type.value,
            "error_message": str(error),
            "attempt": attempt,
        }

        self.error_history.append(error_info)

        logger.warning(
            f"Error in {function_name} (attempt {attempt + 1}): "
            f"{error_type.value} - {error}"
        )

    def retry_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Optional[Callable] = None,
        function_name: str = "unknown",
    ):
        """Decorator for retry logic with optional fallback.

        Args:
            primary_func: Main function to execute.
            fallback_func: Optional fallback function.
            function_name: Name for logging.

        Returns:
            Result of primary_func or fallback_func.
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = primary_func()

                # Log successful recovery if this wasn't the first attempt
                if attempt > 0:
                    logger.info(
                        f"Successfully recovered in {function_name} after {attempt} retries"
                    )

                return result

            except Exception as error:
                last_error = error
                self.log_error(error, attempt, function_name)

                if not self.should_retry(error, attempt):
                    break

                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.info(f"Retrying {function_name} in {delay:.2f} seconds...")
                    time.sleep(delay)

        # All retries failed, try fallback if available
        if fallback_func:
            logger.info(f"Primary function failed, trying fallback for {function_name}")
            try:
                return fallback_func()
            except Exception as fallback_error:
                logger.error(
                    f"Fallback also failed for {function_name}: {fallback_error}"
                )
                raise fallback_error

        # No fallback or fallback failed, raise the last error
        logger.error(f"All attempts failed for {function_name}")
        raise last_error


def with_retry(config: RetryConfig = None, fallback: Callable = None):
    """Decorator for adding retry logic to functions.

    Args:
        config: Retry configuration.
        fallback: Optional fallback function.

    Returns:
        Decorated function with retry logic.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler(config)

            def primary_func():
                return func(*args, **kwargs)

            def fallback_func():
                if fallback:
                    return fallback(*args, **kwargs)
                return None

            return error_handler.retry_with_fallback(
                primary_func, fallback_func if fallback else None, func.__name__
            )

        return wrapper

    return decorator


class GracefulDegradation:
    """Manages graceful degradation of agent functionality."""

    def __init__(self):
        """Initialize graceful degradation manager."""
        self.degradation_level = 0
        self.max_degradation_level = 3

    def increase_degradation(self):
        """Increase degradation level due to errors."""
        if self.degradation_level < self.max_degradation_level:
            self.degradation_level += 1
            logger.warning(f"Increased degradation level to {self.degradation_level}")

    def decrease_degradation(self):
        """Decrease degradation level due to successful operations."""
        if self.degradation_level > 0:
            self.degradation_level -= 1
            logger.info(f"Decreased degradation level to {self.degradation_level}")

    def get_simplified_response(self, user_input: str) -> str:
        """Get a simplified response when normal processing fails.

        Args:
            user_input: User's input message.

        Returns:
            str: Simplified response.
        """
        simple_responses = {
            0: None,  # No degradation
            1: f"I'm experiencing some technical difficulties. Let me try to help you with: {user_input[:50]}...",
            2: "I'm having trouble processing your request right now. Could you try rephrasing or asking something simpler?",
            3: "I'm currently experiencing technical issues. Please try again later or contact support.",
        }

        return simple_responses.get(self.degradation_level)

    def should_use_tools(self) -> bool:
        """Check if tools should be used based on degradation level.

        Returns:
            bool: True if tools can be used.
        """
        return self.degradation_level < 2

    def should_use_advanced_features(self) -> bool:
        """Check if advanced features should be used.

        Returns:
            bool: True if advanced features can be used.
        """
        return self.degradation_level < 1


class UserFeedbackManager:
    """Manages user feedback during error conditions."""

    @staticmethod
    def get_error_message(error_type: ErrorType, is_retry: bool = False) -> str:
        """Get user-friendly error message.

        Args:
            error_type: Type of error.
            is_retry: Whether this is a retry attempt.

        Returns:
            str: User-friendly error message.
        """
        retry_prefix = "Retrying... " if is_retry else ""

        messages = {
            ErrorType.API_ERROR: f"{retry_prefix}Having trouble connecting to the AI service. Please wait...",
            ErrorType.RATE_LIMIT: f"{retry_prefix}Too many requests. Taking a brief pause...",
            ErrorType.NETWORK_ERROR: f"{retry_prefix}Network connectivity issue. Attempting to reconnect...",
            ErrorType.TIMEOUT_ERROR: f"{retry_prefix}Request timed out. Trying again...",
            ErrorType.VALIDATION_ERROR: "There was an issue with your request format. Please try rephrasing.",
            ErrorType.UNKNOWN_ERROR: f"{retry_prefix}Unexpected error occurred. Working to resolve it...",
        }

        return messages.get(
            error_type, f"{retry_prefix}An error occurred. Please try again."
        )

    @staticmethod
    def get_recovery_message() -> str:
        """Get message for successful recovery.

        Returns:
            str: Recovery message.
        """
        return "✅ Connection restored. Continuing with your request..."

    @staticmethod
    def get_fallback_message() -> str:
        """Get message when using fallback functionality.

        Returns:
            str: Fallback message.
        """
        return "🔄 Using alternative approach to help you..."


def create_robust_function(
    func: Callable,
    retry_config: RetryConfig = None,
    fallback_func: Callable = None,
    degradation_manager: GracefulDegradation = None,
) -> Callable:
    """Create a robust version of a function with comprehensive error handling.

    Args:
        func: Original function.
        retry_config: Retry configuration.
        fallback_func: Optional fallback function.
        degradation_manager: Graceful degradation manager.

    Returns:
        Callable: Robust version of the function.
    """
    if not retry_config:
        retry_config = RetryConfig()

    if not degradation_manager:
        degradation_manager = GracefulDegradation()

    error_handler = ErrorHandler(retry_config)

    @wraps(func)
    def robust_wrapper(*args, **kwargs):
        try:

            def primary_func():
                return func(*args, **kwargs)

            def enhanced_fallback():
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                else:
                    # Generic fallback behavior
                    degradation_manager.increase_degradation()
                    if hasattr(args[0], "get") and "user_input" in args[0]:
                        return degradation_manager.get_simplified_response(
                            args[0]["user_input"]
                        )
                    return "I'm experiencing technical difficulties. Please try again."

            result = error_handler.retry_with_fallback(
                primary_func, enhanced_fallback, func.__name__
            )

            # Decrease degradation on successful operation
            degradation_manager.decrease_degradation()

            return result

        except Exception as e:
            logger.error(f"All recovery attempts failed for {func.__name__}: {e}")
            degradation_manager.increase_degradation()
            raise

    return robust_wrapper
