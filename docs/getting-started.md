# Getting Started with Bob LangGraph Agent

This guide will help you get Bob up and running quickly.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.12+** installed on your system
- **uv** package manager ([installation guide](https://github.com/astral-sh/uv))
- **Anthropic API key** (get one at [Anthropic Console](https://console.anthropic.com/))

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/HuyNguyen260398/bob_langgraph_agent.git
cd bob_langgraph_agent
```

### 2. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

### 3. Configure Environment

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` file:
```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional (defaults provided)
ANTHROPIC_MODEL_NAME=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=0.7
```

## Quick Test

### Interactive Chat

Run the interactive chat interface:

```bash
uv run bob-agent
```

You should see:
```
🤖 Bob LangGraph Agent - Your AI Operations Buddy!
==================================================
✅ Loaded configuration (Model: claude-3-5-sonnet-20241022)
✅ Agent initialized successfully!

💬 Starting interactive chat (type 'quit' to exit)
--------------------------------------------------

👤 You: 
```

### Programmatic Usage

Create a simple Python script:

```python
# test_bob.py
from bob_langgraph_agent import BobAgent, BobConfig

def test_bob():
    # Load configuration from environment
    config = BobConfig.from_env()
    
    # Create agent
    agent = BobAgent(config)
    
    # Test conversation
    response = agent.chat("Hello Bob! Tell me about yourself.")
    print(f"Bob says: {response}")

if __name__ == "__main__":
    test_bob()
```

Run it:
```bash
uv run python test_bob.py
```

## Basic Usage Examples

### Single Message

```python
from bob_langgraph_agent import BobAgent, BobConfig

config = BobConfig.from_env()
agent = BobAgent(config)

response = agent.chat("What can you help me with?")
print(response)
```

### Conversation with History

```python
# Messages are automatically tracked per thread
agent = BobAgent(config)

# First message
response1 = agent.chat("My name is Alice", thread_id="alice_session")

# Second message (Bob remembers the context)
response2 = agent.chat("What's my name?", thread_id="alice_session")
```

### Streaming Responses

```python
agent = BobAgent(config)

for update in agent.stream_chat("Tell me a story", thread_id="story_session"):
    print(update)
```

## Troubleshooting

### Common Issues

1. **"ANTHROPIC_API_KEY must be provided"**
   - Make sure your `.env` file contains a valid API key
   - Verify the key is correctly formatted (no extra spaces)

2. **"ModuleNotFoundError"**
   - Ensure you've run `uv sync` to install dependencies
   - Activate the virtual environment if needed

3. **API Rate Limits**
   - Check your Anthropic account usage limits
   - Consider reducing `ANTHROPIC_MAX_TOKENS` if needed

### Getting Help

- Check the [API Reference](api-reference.md) for detailed documentation
- Review [Configuration](configuration.md) for advanced settings
- Browse [Examples](examples.md) for more use cases

## Next Steps

Now that Bob is running:

1. **Explore Configuration**: Learn about [configuration options](configuration.md)
2. **Try Examples**: Check out more [usage examples](examples.md)
3. **Understand Architecture**: Read about the [system design](architecture.md)
4. **Deploy**: Follow the [deployment guide](deployment.md) for production use

Happy chatting with Bob! 🤖