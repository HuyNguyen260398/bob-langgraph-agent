# Bob LangGraph Agent 🤖

**DevOps Buddy** - An AI agent built with LangGraph framework and powered by Anthropic's Claude model.

## Overview

Bob is a conversational AI agent designed to be your operations buddy. Built using the powerful LangGraph framework, Bob provides intelligent, context-aware responses while maintaining conversation history and state management.

## Features

- 🧠 **Powered by Claude**: Uses Anthropic's advanced Claude-3.5-Sonnet model
- 🔄 **State Management**: LangGraph-based workflow with conversation persistence
- 💬 **Interactive Chat**: Command-line interface for real-time conversations
- 🛠️ **Function Calling**: Built-in tools for math, text processing, note-taking, and more
- 🎯 **Advanced Workflow**: Conversation analysis, summarization, and planning
- ⚙️ **Configurable**: Easy configuration via environment variables or code
- 🛡️ **Robust Error Handling**: Retry logic, graceful degradation, and fallbacks
- 📦 **Modern Python**: Built with Python 3.12+ and managed by uv
- 🏗️ **Modular Design**: Clean separation of concerns with extensible architecture

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Anthropic API key

### Installation

1. **Clone the repository**:

```bash
git clone https://github.com/HuyNguyen260398/bob_langgraph_agent.git
cd bob_langgraph_agent

```

2. **Install dependencies**:

```bash
uv sync

```

3. **Set up environment variables**:

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

```

4. **Run the agent**:

```bash
uv run bob-agent

```

### Docker Deployment 🐳

**Quick Start with Docker:**

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Build and start
docker-compose up -d

# 3. Test the API
curl http://localhost:8000/health
```

**Access the API:**
- Interactive Docs: http://localhost:8000/docs
- Chat Endpoint: `POST http://localhost:8000/chat`

See [Docker Quick Start](DOCKER_QUICKSTART.md) for detailed instructions and [Deployment Guide](docs/DEPLOYMENT.md) for production deployment.

### Basic Usage

```python
from bob_langgraph_agent import BobAgent, BobConfig

# Create configuration
config = BobConfig.from_env()

# Initialize agent
agent = BobAgent(config)

# Chat with Bob
response = agent.chat("Hello Bob, how are you?")
print(response)

```

## Project Structure

```ini
bob_langgraph_agent/
├── src/
│   └── bob_langgraph_agent/
│       ├── __init__.py          # Package initialization
│       ├── agent.py             # Main agent implementation
│       ├── config.py            # Configuration management
│       ├── state.py             # State management
│       └── main.py              # CLI entry point
├── docs/                        # Documentation
├── .env.example                 # Environment variables template
├── pyproject.toml              # Project configuration
└── README.md                   # This file

```

## Configuration

Bob can be configured through environment variables or programmatically:

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | __Required__ |
| `ANTHROPIC_MODEL_NAME` | Claude model to use | `claude-3-5-sonnet-20241022` |
| `ANTHROPIC_MAX_TOKENS` | Maximum tokens in response | `4096` |
| `ANTHROPIC_TEMPERATURE` | Response creativity (0-1) | `0.7` |
| `AGENT_NAME` | Agent's name | `Bob` |
| `SYSTEM_MESSAGE` | System prompt | `You are Bob, a helpful AI assistant...` |
| `MAX_ITERATIONS` | Max conversation iterations | `10` |
| `MAX_CONVERSATION_HISTORY` | Max messages to keep in memory | `20` |
| `MAX_RETRIES` | Max retry attempts for failed requests | `3` |
| `RETRY_BASE_DELAY` | Base delay between retries (seconds) | `1.0` |
| `RETRY_MAX_DELAY` | Maximum delay between retries (seconds) | `60.0` |

### Programmatic Configuration

```python
from bob_langgraph_agent import BobConfig

config = BobConfig(
    anthropic_api_key="your-key-here",
    model_name="claude-3-5-sonnet-20241022",
    temperature=0.8,
    agent_name="CustomBob"
)

```

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/HuyNguyen260398/bob_langgraph_agent.git
cd bob_langgraph_agent

# Install in development mode
uv sync --dev

# Run tests (when available)
uv run pytest

# Run the agent
uv run python -m bob_langgraph_agent.main

```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for workflow management
- Powered by [Anthropic Claude](https://www.anthropic.com/) for intelligent responses
- Package management by [uv](https://github.com/astral-sh/uv)
