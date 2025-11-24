"""Tools for Bob LangGraph Agent."""

import json
import time
from datetime import datetime
from typing import Any, Dict, List

from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """Get the current date and time.

    Returns:
        str: Current date and time in a readable format.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def get_current_date() -> str:
    """Get the current date.

    Returns:
        str: Current date in YYYY-MM-DD format.
    """
    return datetime.now().strftime("%Y-%m-%d")


@tool
def calculate_math(expression: str) -> str:
    """Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate (supports +, -, *, /, **, (), basic functions)

    Returns:
        str: Result of the calculation or error message.
    """
    try:
        # Only allow safe operations
        allowed_names = {
            k: v
            for k, v in __builtins__.items()
            if k in ("abs", "round", "min", "max", "sum", "pow")
        }
        allowed_names.update(
            {
                "pi": 3.14159265359,
                "e": 2.71828182846,
            }
        )

        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


@tool
def format_text(text: str, style: str = "upper") -> str:
    """Format text in different styles.

    Args:
        text: Text to format
        style: Style to apply (upper, lower, title, capitalize)

    Returns:
        str: Formatted text.
    """
    style = style.lower()
    if style == "upper":
        return text.upper()
    elif style == "lower":
        return text.lower()
    elif style == "title":
        return text.title()
    elif style == "capitalize":
        return text.capitalize()
    else:
        return f"Unknown style '{style}'. Available: upper, lower, title, capitalize"


@tool
def search_text(text: str, pattern: str) -> str:
    """Search for a pattern in text.

    Args:
        text: Text to search in
        pattern: Pattern to search for

    Returns:
        str: Information about the search results.
    """
    import re

    # Simple case-insensitive search
    matches = re.findall(pattern, text, re.IGNORECASE)
    count = len(matches)

    if count == 0:
        return f"Pattern '{pattern}' not found in the text."
    elif count == 1:
        return f"Pattern '{pattern}' found 1 time in the text."
    else:
        return f"Pattern '{pattern}' found {count} times in the text."


@tool
def save_note(content: str, title: str = None) -> str:
    """Save a note to a simple text file.

    Args:
        content: Content of the note
        title: Optional title for the note

    Returns:
        str: Confirmation message.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"note_{timestamp}.txt"

        if title:
            full_content = f"Title: {title}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}"
        else:
            full_content = (
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}"
            )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_content)

        return f"Note saved to {filename}"
    except Exception as e:
        return f"Error saving note: {str(e)}"


# List of all available tools
AVAILABLE_TOOLS = [
    get_current_time,
    get_current_date,
    calculate_math,
    format_text,
    search_text,
    save_note,
]


def get_tools() -> List[Any]:
    """Get all available tools.

    Returns:
        List of tool functions.
    """
    return AVAILABLE_TOOLS


def get_tool_descriptions() -> Dict[str, str]:
    """Get descriptions of all available tools.

    Returns:
        Dict mapping tool names to their descriptions.
    """
    descriptions = {}
    for tool in AVAILABLE_TOOLS:
        descriptions[tool.name] = tool.description
    return descriptions
