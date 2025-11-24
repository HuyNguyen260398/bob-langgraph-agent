# Bob LangGraph Agent - Deployment Guide

This guide covers how to deploy the Bob LangGraph Agent in various environments, starting with Docker containerization.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Production Deployment Considerations](#production-deployment-considerations)
- [API Documentation](#api-documentation)
- [Monitoring and Logging](#monitoring-and-logging)

---

## Docker Deployment

### Prerequisites

- Docker installed (version 20.10 or higher)
- Docker Compose (optional, for multi-container setup)
- Anthropic API key

### Quick Start with Docker

1. **Set up environment variables:**

   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your Anthropic API key
   nano .env
   ```

2. **Build the Docker image:**

   ```bash
   docker build -t bob-langgraph-agent:latest .
   ```

3. **Run the container:**

   ```bash
   docker run -d \
     --name bob-agent \
     -p 8000:8000 \
     --env-file .env \
     bob-langgraph-agent:latest
   ```

4. **Check if the agent is running:**

   ```bash
   curl http://localhost:8000/health
   ```

### Docker Build Options

**Development build (with volume mounting):**

```bash
docker run -d \
  --name bob-agent-dev \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/src:/app/src:ro \
  bob-langgraph-agent:latest
```

**Production build (minimal image):**

```bash
# Build with optimization
docker build \
  --target production \
  -t bob-langgraph-agent:prod \
  .

# Run with resource limits
docker run -d \
  --name bob-agent-prod \
  -p 8000:8000 \
  --env-file .env \
  --memory="2g" \
  --cpus="2.0" \
  --restart unless-stopped \
  bob-langgraph-agent:prod
```

---

## Docker Compose Deployment

Docker Compose simplifies multi-container deployments and configuration management.

### Basic Deployment

1. **Start the services:**

   ```bash
   docker-compose up -d
   ```

2. **View logs:**

   ```bash
   docker-compose logs -f bob-agent
   ```

3. **Stop the services:**

   ```bash
   docker-compose down
   ```

### Production Docker Compose

For production, you can extend the basic `docker-compose.yml`:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  bob-agent:
    extends:
      file: docker-compose.yml
      service: bob-agent
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Run with:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Production Deployment Considerations

### 1. Security

**Environment Variables:**
- Never commit `.env` files with secrets
- Use Docker secrets or environment variable injection from your orchestration platform
- Rotate API keys regularly

**Container Security:**
- Run as non-root user (already configured in Dockerfile)
- Use read-only file systems where possible
- Scan images for vulnerabilities

**Network Security:**
- Use HTTPS/TLS for all external communication
- Configure CORS appropriately
- Implement rate limiting
- Add authentication middleware

### 2. Scalability

**Horizontal Scaling:**

```bash
# Scale to 3 instances
docker-compose up -d --scale bob-agent=3
```

**Load Balancing:**
- Add nginx or Traefik as reverse proxy
- Configure health checks
- Implement session stickiness for conversation threads

### 3. Persistence

The agent uses in-memory state by default. For production:

**Add Redis for state persistence:**

```yaml
services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  bob-agent:
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

volumes:
  redis-data:
```

**Add PostgreSQL for conversation history:**

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=bob_agent
      - POSTGRES_USER=bob
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

### 4. Monitoring

**Health Checks:**
```bash
# Built-in health endpoint
curl http://localhost:8000/health

# Docker health check (configured in Dockerfile)
docker inspect --format='{{.State.Health.Status}}' bob-agent
```

**Logging:**
```bash
# View logs
docker-compose logs -f bob-agent

# Configure log aggregation (ELK, Datadog, etc.)
```

**Metrics:**
- Add Prometheus metrics endpoint
- Configure application performance monitoring (APM)
- Track conversation metrics and response times

---

## API Documentation

Once deployed, access the interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

#### Chat Endpoint
```bash
POST /chat
Content-Type: application/json

{
  "message": "Hello Bob!",
  "thread_id": "user-123"
}
```

#### Streaming Chat
```bash
POST /chat/stream
Content-Type: application/json

{
  "message": "Tell me a story",
  "thread_id": "user-123"
}
```

#### Get Conversation History
```bash
GET /history/{thread_id}
```

#### Get Conversation Summary
```bash
GET /summary/{thread_id}
```

#### Clear Thread
```bash
DELETE /thread/{thread_id}
```

### Example Client Usage

**Python:**
```python
import requests

# Chat with Bob
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "What can you help me with?",
        "thread_id": "my-session"
    }
)

print(response.json()["response"])
```

**cURL:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "thread_id": "test"}'
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello Bob!',
    thread_id: 'web-user-123'
  })
});

const data = await response.json();
console.log(data.response);
```

---

## Monitoring and Logging

### Application Logs

**View real-time logs:**
```bash
docker-compose logs -f bob-agent
```

**Export logs:**
```bash
docker logs bob-agent > agent-logs.txt
```

### Resource Monitoring

**Check resource usage:**
```bash
docker stats bob-agent
```

**Monitor multiple containers:**
```bash
docker-compose ps
docker-compose top
```

### Health Monitoring

**Automated health checks:**
```bash
# Check every 30 seconds
while true; do
  curl -f http://localhost:8000/health || echo "Health check failed"
  sleep 30
done
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs bob-agent

# Check if port is already in use
netstat -an | grep 8000

# Inspect container
docker inspect bob-agent
```

### API Key Issues

```bash
# Verify environment variables
docker exec bob-agent env | grep ANTHROPIC

# Test API key
docker exec bob-agent python -c "import os; print(os.getenv('ANTHROPIC_API_KEY')[:10])"
```

### Performance Issues

```bash
# Check resource usage
docker stats bob-agent

# Increase memory limit
docker update --memory 4g bob-agent

# Check application logs for errors
docker logs bob-agent --tail 100
```

---

## Next Steps

- [Kubernetes Deployment](./KUBERNETES_DEPLOYMENT.md) - Deploy at scale with K8s
- [Cloud Deployment](./CLOUD_DEPLOYMENT.md) - AWS, GCP, Azure options
- [CI/CD Pipeline](./CICD.md) - Automated deployments
- [Monitoring Setup](./MONITORING.md) - Advanced monitoring and alerting

---

## Support

For issues or questions:
- Check the [FAQ](./FAQ.md)
- Review the [API documentation](http://localhost:8000/docs)
- Open an issue on GitHub
