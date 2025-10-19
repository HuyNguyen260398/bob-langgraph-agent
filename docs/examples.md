# Usage Examples

This document provides practical examples of using Bob LangGraph Agent in different scenarios.

## Basic Usage

### Simple Chat

```python
from bob_langgraph_agent import BobAgent, BobConfig

# Setup
config = BobConfig.from_env()
agent = BobAgent(config)

# Single interaction
response = agent.chat("Hello Bob! How are you today?")
print(response)
```

### Conversation with Context

```python
# Messages are automatically tracked per thread
agent = BobAgent(config)

# First message
agent.chat("My name is Alice and I work as a DevOps engineer", thread_id="alice")

# Second message (Bob remembers context)
response = agent.chat("What's my job?", thread_id="alice")
print(response)  # Bob will remember Alice is a DevOps engineer
```

## Advanced Usage

### Multiple Conversations

```python
agent = BobAgent(config)

# Customer support conversations
agent.chat("I'm having trouble with deployment", thread_id="customer_1")
agent.chat("The build is failing", thread_id="customer_2")

# Each conversation maintains separate context
response1 = agent.chat("Can you summarize my issue?", thread_id="customer_1")
response2 = agent.chat("What was my problem again?", thread_id="customer_2")
```

### Streaming Responses

```python
agent = BobAgent(config)

print("User: Tell me about Docker containers")
print("Bob: ", end="", flush=True)

for update in agent.stream_chat("Tell me about Docker containers"):
    if "generate_response" in update:
        # Extract and print partial response
        response = update["generate_response"].get("agent_response", "")
        if response:
            print(response, end="", flush=True)

print()  # New line after complete response
```

### Conversation History

```python
agent = BobAgent(config)

# Have a conversation
agent.chat("I'm working on a Python project", thread_id="dev_session")
agent.chat("I need help with testing", thread_id="dev_session")

# Get conversation history
history = agent.get_conversation_history(thread_id="dev_session")
for message in history:
    print(f"{message.__class__.__name__}: {message.content}")
```

## Specialized Use Cases

### Code Review Assistant

```python
from bob_langgraph_agent import BobConfig, BobAgent

# Configure for code review
config = BobConfig(
    anthropic_api_key="your-key",
    system_message="""You are a senior software engineer helping with code reviews. 
    Provide constructive feedback focusing on:
    - Code quality and best practices
    - Potential bugs or issues
    - Performance improvements
    - Security considerations
    - Maintainability""",
    temperature=0.3,  # More consistent
    agent_name="Code Reviewer"
)

agent = BobAgent(config)

code = '''
def process_user_input(user_data):
    sql = f"SELECT * FROM users WHERE name = '{user_data['name']}'"
    return execute_query(sql)
'''

response = agent.chat(f"Please review this Python code:\n\n{code}")
print(response)
```

### DevOps Troubleshooting

```python
config = BobConfig(
    anthropic_api_key="your-key",
    system_message="""You are an experienced DevOps engineer. Help users with:
    - Infrastructure issues
    - CI/CD pipeline problems
    - Container and orchestration issues
    - Monitoring and logging
    - Security best practices
    
    Always ask clarifying questions when needed.""",
    agent_name="DevOps Assistant"
)

agent = BobAgent(config)

# Start troubleshooting session
response = agent.chat(
    "My Kubernetes pod keeps crashing with exit code 137",
    thread_id="k8s_troubleshooting"
)
print(response)

# Follow up with more details
response = agent.chat(
    "The pod has 512Mi memory limit and runs a Java application",
    thread_id="k8s_troubleshooting"
)
print(response)
```

### Documentation Helper

```python
config = BobConfig(
    anthropic_api_key="your-key",
    system_message="""You are a technical writing assistant. Help users create:
    - Clear, concise documentation
    - API documentation
    - User guides and tutorials
    - README files
    - Technical specifications
    
    Focus on clarity, completeness, and user-friendliness.""",
    agent_name="Doc Helper"
)

agent = BobAgent(config)

response = agent.chat(
    "Help me write documentation for a REST API that manages user accounts",
    thread_id="api_docs"
)
print(response)
```

## CLI Usage

### Interactive Mode

```bash
# Start interactive chat
uv run bob-agent

# Example session:
# 👤 You: Hello Bob, I need help with Docker
# 🤖 Bob: Hello! I'd be happy to help you with Docker...
# 👤 You: How do I create a Dockerfile for a Python app?
# 🤖 Bob: Here's how to create a Dockerfile for a Python application...
```

### Programmatic CLI Usage

```python
from bob_langgraph_agent.main import demo_chat

# Quick demo with custom message
demo_chat("Explain the difference between Docker and Podman")
```

## Error Handling

### Graceful Error Handling

```python
from bob_langgraph_agent import BobAgent, BobConfig

try:
    config = BobConfig.from_env()
    agent = BobAgent(config)
    
    response = agent.chat("Hello Bob!")
    print(response)
    
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Handling Rate Limits

```python
import time
from anthropic import RateLimitError

agent = BobAgent(config)

def chat_with_retry(message, thread_id="default", max_retries=3):
    for attempt in range(max_retries):
        try:
            return agent.chat(message, thread_id)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise
    
# Usage
response = chat_with_retry("Hello Bob!")
```

## Integration Examples

### Flask Web Application

```python
from flask import Flask, request, jsonify
from bob_langgraph_agent import BobAgent, BobConfig

app = Flask(__name__)
config = BobConfig.from_env()
agent = BobAgent(config)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    thread_id = data.get('thread_id', 'web_session')
    
    try:
        response = agent.chat(message, thread_id)
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Discord Bot Integration

```python
import discord
from discord.ext import commands
from bob_langgraph_agent import BobAgent, BobConfig

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

config = BobConfig.from_env()
agent = BobAgent(config)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='ask')
async def ask_bob(ctx, *, question):
    """Ask Bob a question"""
    thread_id = f"discord_{ctx.author.id}"
    
    try:
        response = agent.chat(question, thread_id)
        await ctx.send(f"🤖 **Bob**: {response}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# bot.run('your-discord-token')
```

## Best Practices

### Memory Management

```python
# For long-running applications, consider conversation cleanup
def cleanup_old_conversations(agent, max_age_hours=24):
    """Clean up old conversation threads"""
    # Implementation depends on your specific needs
    # This is a conceptual example
    pass

# Periodic cleanup
import threading
import time

def periodic_cleanup():
    while True:
        time.sleep(3600)  # Every hour
        cleanup_old_conversations(agent)

cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

### Configuration Management

```python
# Use different configs for different environments
import os

def get_config():
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        return BobConfig(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            temperature=0.5,  # More consistent in production
            max_iterations=8
        )
    else:
        return BobConfig.from_env()

config = get_config()
agent = BobAgent(config)
```

### Logging and Monitoring

```python
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoredBobAgent(BobAgent):
    def chat(self, message, thread_id="default"):
        logger.info(f"Chat request - Thread: {thread_id}, Message length: {len(message)}")
        
        try:
            response = super().chat(message, thread_id)
            logger.info(f"Chat response - Thread: {thread_id}, Response length: {len(response)}")
            return response
        except Exception as e:
            logger.error(f"Chat error - Thread: {thread_id}, Error: {e}")
            raise

# Use monitored agent
agent = MonitoredBobAgent(config)
```

These examples should give you a solid foundation for integrating Bob LangGraph Agent into your applications!