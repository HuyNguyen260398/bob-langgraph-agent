# Docker Deployment Files for Bob LangGraph Agent

This directory contains all the necessary files for deploying the Bob LangGraph Agent using Docker.

## Files Overview

### Core Deployment Files

- **`Dockerfile`** - Multi-stage Docker image definition for the agent
- **`docker-compose.yml`** - Docker Compose configuration for local/development deployment
- **`.dockerignore`** - Files to exclude from Docker build context
- **`.env.example`** - Template for environment variables

### API & Server

- **`src/bob_langgraph_agent/api.py`** - FastAPI server implementation
  - RESTful API endpoints
  - Health checks
  - Streaming support
  - Conversation management

### Scripts

- **`scripts/build-docker.ps1`** - PowerShell script to build and test Docker image (Windows)
- **`scripts/deploy.sh`** - Bash script for deployment management (Linux/Mac)
- **`scripts/start.ps1`** - Quick start script for Windows

### Testing

- **`test_api.py`** - Comprehensive API testing script
  - Tests all endpoints
  - Validates functionality
  - Provides clear output

### Documentation

- **`docs/DEPLOYMENT.md`** - Complete deployment guide with production considerations
- **`DOCKER_QUICKSTART.md`** - Quick start guide for Docker deployment

## Quick Reference

### Build & Deploy

```bash
# Quick start (Windows PowerShell)
.\scripts\start.ps1

# Or using Docker Compose
docker-compose up -d

# Build from scratch
docker build -t bob-langgraph-agent:latest .
```

### Test

```bash
# Check health
curl http://localhost:8000/health

# Run comprehensive tests
python test_api.py

# View API docs
# Open: http://localhost:8000/docs
```

### Manage

```bash
# View logs
docker-compose logs -f bob-agent

# Stop services
docker-compose down

# Restart
docker-compose restart

# Check status
docker-compose ps
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Client Applications              │
│   (Browser, cURL, Python, JavaScript)   │
└────────────────┬────────────────────────┘
                 │ HTTP/REST
                 │
┌────────────────▼────────────────────────┐
│         FastAPI Server (Port 8000)       │
│  • /chat - Chat endpoint                │
│  • /chat/stream - Streaming responses    │
│  • /history - Conversation history       │
│  • /summary - Conversation summary       │
│  • /analysis - Conversation analysis     │
│  • /health - Health check                │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Bob LangGraph Agent              │
│  • State management (InMemorySaver)     │
│  • LangGraph workflow execution          │
│  • Tool calling                          │
│  • Error handling & retries              │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Anthropic Claude API                │
│  (claude-sonnet-4-5-20250929)           │
└─────────────────────────────────────────┘
```

## Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Your Anthropic API key

Optional:
- `BOB_MODEL_NAME` - Model to use (default: claude-sonnet-4-5-20250929)
- `BOB_MAX_TOKENS` - Max response tokens (default: 4096)
- `BOB_TEMPERATURE` - Response temperature (default: 0.7)
- `BOB_MAX_ITERATIONS` - Max workflow iterations (default: 10)
- `BOB_MAX_CONVERSATION_HISTORY` - Max messages to keep (default: 50)

## Production Considerations

1. **Security**
   - Use secrets management (not .env files)
   - Enable HTTPS/TLS
   - Add authentication middleware
   - Configure CORS appropriately

2. **Scalability**
   - Use external state management (Redis/PostgreSQL)
   - Deploy behind load balancer
   - Scale horizontally with Kubernetes
   - Implement connection pooling

3. **Monitoring**
   - Add Prometheus metrics
   - Configure logging aggregation
   - Set up health check monitoring
   - Track API usage and costs

4. **Persistence**
   - Replace InMemorySaver with Redis
   - Add PostgreSQL for conversation history
   - Implement backup strategies

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed production deployment guide.

## Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use 8001 instead
   ```

2. **API key not found**
   ```bash
   # Verify .env file
   cat .env | grep ANTHROPIC_API_KEY
   
   # Restart container
   docker-compose restart
   ```

3. **Container health check failing**
   ```bash
   # Check logs
   docker-compose logs bob-agent
   
   # Check container status
   docker inspect bob-agent
   ```

## Next Steps

- [Production Deployment Guide](docs/DEPLOYMENT.md)
- [API Documentation](http://localhost:8000/docs)
- [Configuration Options](docs/configuration.md)
- [Examples & Integration Patterns](examples/)
