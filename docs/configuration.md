# Configuration Guide

This guide covers all configuration options available for Bob LangGraph Agent.

## Environment Variables

The agent can be configured using environment variables. Create a `.env` file in your project root:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-api03-...` |

### Optional Variables

| Variable | Description | Default | Valid Values |
|----------|-------------|---------|--------------|
| `ANTHROPIC_MODEL_NAME` | Claude model to use | `claude-3-5-sonnet-20241022` | See [Anthropic Models](https://docs.anthropic.com/claude/docs/models-overview) |
| `ANTHROPIC_MAX_TOKENS` | Maximum tokens in response | `4096` | `1` to `8192` |
| `ANTHROPIC_TEMPERATURE` | Response creativity | `0.7` | `0.0` to `1.0` |
| `AGENT_NAME` | Agent's display name | `Bob` | Any string |
| `SYSTEM_MESSAGE` | System prompt for the agent | `You are Bob, a helpful...` | Any string |
| `MAX_ITERATIONS` | Max conversation iterations | `10` | Positive integer |

## Programmatic Configuration

You can also configure the agent programmatically:

### Basic Configuration

```python
from bob_langgraph_agent import BobConfig

# Using environment variables
config = BobConfig.from_env()

# Direct configuration
config = BobConfig(
    anthropic_api_key="your-api-key",
    model_name="claude-3-5-sonnet-20241022",
    max_tokens=2048,
    temperature=0.5
)
```

### Custom System Message

```python
config = BobConfig(
    anthropic_api_key="your-api-key",
    system_message="You are a specialized DevOps assistant. Help users with infrastructure, deployment, and automation tasks."
)
```

### Advanced Configuration

```python
config = BobConfig(
    anthropic_api_key="your-api-key",
    model_name="claude-3-haiku-20240307",  # Faster, cheaper model
    max_tokens=1024,
    temperature=0.3,  # More deterministic
    agent_name="DevOps Bot",
    max_iterations=5  # Shorter conversations
)
```

## Model Selection Guide

### Claude 3.5 Sonnet (Recommended)
- **Model**: `claude-3-5-sonnet-20241022`
- **Best for**: General conversation, complex reasoning
- **Speed**: Medium
- **Cost**: Medium

### Claude 3 Haiku
- **Model**: `claude-3-haiku-20240307`
- **Best for**: Quick responses, simple tasks
- **Speed**: Fast
- **Cost**: Low

### Claude 3 Opus
- **Model**: `claude-3-opus-20240229`
- **Best for**: Complex analysis, creative tasks
- **Speed**: Slow
- **Cost**: High

## Temperature Guidelines

- **0.0 - 0.3**: Highly deterministic, consistent responses
- **0.4 - 0.7**: Balanced creativity and consistency (recommended)
- **0.8 - 1.0**: More creative, varied responses

## Configuration Validation

The configuration system automatically validates:

- **API Key**: Must be provided and non-empty
- **Max Tokens**: Must be between 1 and model limit
- **Temperature**: Must be between 0.0 and 1.0
- **Max Iterations**: Must be positive integer

## Configuration Examples

### Production Environment

```bash
# .env.production
ANTHROPIC_API_KEY=sk-ant-api03-production-key
ANTHROPIC_MODEL_NAME=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=0.7
AGENT_NAME=Bob Production
SYSTEM_MESSAGE=You are Bob, a professional AI assistant for our production environment.
MAX_ITERATIONS=10
```

### Development Environment

```bash
# .env.development
ANTHROPIC_API_KEY=sk-ant-api03-development-key
ANTHROPIC_MODEL_NAME=claude-3-haiku-20240307
ANTHROPIC_MAX_TOKENS=2048
ANTHROPIC_TEMPERATURE=0.8
AGENT_NAME=Bob Dev
SYSTEM_MESSAGE=You are Bob, a development AI assistant. Be helpful and explain your reasoning.
MAX_ITERATIONS=15
```

### Specialized Use Cases

```python
# Customer Support Bot
config = BobConfig(
    anthropic_api_key="your-key",
    system_message="You are a helpful customer support assistant. Be empathetic, professional, and solution-focused.",
    temperature=0.4,  # More consistent
    agent_name="Support Bot"
)

# Code Review Assistant
config = BobConfig(
    anthropic_api_key="your-key",
    system_message="You are a senior software engineer helping with code reviews. Provide constructive feedback and best practices.",
    temperature=0.3,  # Very consistent
    max_tokens=6000,  # Longer code explanations
    agent_name="Code Reviewer"
)
```

## Troubleshooting

### Common Issues

1. **"ANTHROPIC_API_KEY must be provided"**
   - Check your `.env` file exists and contains the key
   - Verify no extra spaces around the key value
   - Ensure the key starts with `sk-ant-api03-`

2. **"Invalid model name"**
   - Check the model name against [Anthropic's documentation](https://docs.anthropic.com/claude/docs/models-overview)
   - Ensure exact spelling and case sensitivity

3. **Rate limiting errors**
   - Reduce `max_tokens` or increase delays between requests
   - Check your Anthropic account usage limits

4. **Unexpected responses**
   - Adjust `temperature` for more/less creativity
   - Modify `system_message` for better context
   - Check `max_tokens` isn't too low for complete responses