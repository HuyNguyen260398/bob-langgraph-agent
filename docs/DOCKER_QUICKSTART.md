# Quick Start - Docker Deployment

This guide will get you up and running with Bob LangGraph Agent in Docker in under 5 minutes.

## Prerequisites

- Docker Desktop installed and running
- Anthropic API key

## Steps

### 1. Clone and Configure

```bash
# Navigate to the project directory
cd bob-langgraph-agent

# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key (use notepad, vim, or any editor)
notepad .env  # Windows
# or
nano .env     # Linux/Mac
```

Add your Anthropic API key to the `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
```

### 2. Build and Start

**Option A: Using Docker Compose (Recommended)**

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f bob-agent
```

**Option B: Using Docker Directly**

```bash
# Build the image
docker build -t bob-langgraph-agent:latest .

# Run the container
docker run -d \
  --name bob-agent \
  -p 8000:8000 \
  --env-file .env \
  bob-langgraph-agent:latest
```

**Option C: Using PowerShell Script (Windows)**

```powershell
# Build and test
.\scripts\build-docker.ps1

# Deploy
docker-compose up -d
```

### 3. Test the API

**Check if it's running:**

```bash
# Health check
curl http://localhost:8000/health

# View API documentation
# Open in browser: http://localhost:8000/docs
```

**Send a test message:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Bob!", "thread_id": "test"}'
```

**Run automated tests:**

```bash
# Using Python
python test_api.py

# Or using uv
uv run test_api.py
```

### 4. Access the API

- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f bob-agent

# Restart services
docker-compose restart

# Check status
docker-compose ps

# Rebuild after code changes
docker-compose up -d --build
```

## Troubleshooting

**Container won't start:**
```bash
# Check logs
docker logs bob-agent

# Check if port 8000 is available
netstat -an | grep 8000  # Linux/Mac
netstat -an | findstr 8000  # Windows
```

**API key errors:**
```bash
# Verify environment variables
docker exec bob-agent env | grep ANTHROPIC
```

**Performance issues:**
```bash
# Check resource usage
docker stats bob-agent
```

## Next Steps

- Read the [full deployment guide](docs/DEPLOYMENT.md) for production deployment
- Explore the [API documentation](http://localhost:8000/docs)
- Check out [examples](examples/) for integration patterns
- See [configuration options](docs/configuration.md)

## Support

- API docs: http://localhost:8000/docs
- Project README: [README.md](README.md)
- Full deployment guide: [DEPLOYMENT.md](docs/DEPLOYMENT.md)
