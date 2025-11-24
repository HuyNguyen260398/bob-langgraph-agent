#!/bin/bash
# Bash script to deploy Bob LangGraph Agent using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 Bob LangGraph Agent Deployment Script${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}📝 Please edit .env file and add your ANTHROPIC_API_KEY${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
fi

# Parse command line arguments
COMMAND=${1:-up}

case $COMMAND in
    up|start)
        echo -e "${GREEN}🚀 Starting Bob LangGraph Agent...${NC}"
        docker-compose up -d
        
        echo ""
        echo -e "${CYAN}⏳ Waiting for service to be ready...${NC}"
        sleep 5
        
        # Check if service is healthy
        MAX_RETRIES=12
        RETRY_COUNT=0
        
        until curl -f http://localhost:8000/health > /dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
            RETRY_COUNT=$((RETRY_COUNT+1))
            echo -e "${YELLOW}Waiting for service... ($RETRY_COUNT/$MAX_RETRIES)${NC}"
            sleep 5
        done
        
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo -e "${RED}❌ Service failed to start properly${NC}"
            echo ""
            echo -e "${YELLOW}Container logs:${NC}"
            docker-compose logs --tail=50 bob-agent
            exit 1
        fi
        
        echo ""
        echo -e "${GREEN}✅ Bob LangGraph Agent is running!${NC}"
        echo ""
        echo -e "${CYAN}📝 Available endpoints:${NC}"
        echo "  • API Documentation: http://localhost:8000/docs"
        echo "  • Health Check: http://localhost:8000/health"
        echo "  • Chat API: http://localhost:8000/chat"
        echo ""
        echo -e "${CYAN}📊 View logs:${NC}"
        echo "  docker-compose logs -f bob-agent"
        ;;
        
    down|stop)
        echo -e "${YELLOW}🛑 Stopping Bob LangGraph Agent...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}🔄 Restarting Bob LangGraph Agent...${NC}"
        docker-compose restart
        echo -e "${GREEN}✅ Services restarted${NC}"
        ;;
        
    logs)
        docker-compose logs -f bob-agent
        ;;
        
    build)
        echo -e "${CYAN}🔨 Building Docker image...${NC}"
        docker-compose build
        echo -e "${GREEN}✅ Build complete${NC}"
        ;;
        
    rebuild)
        echo -e "${CYAN}🔨 Rebuilding Docker image (no cache)...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}✅ Rebuild complete${NC}"
        ;;
        
    status)
        echo -e "${CYAN}📊 Service Status:${NC}"
        docker-compose ps
        echo ""
        echo -e "${CYAN}🔍 Health Check:${NC}"
        curl -s http://localhost:8000/health | python3 -m json.tool || echo "Service not responding"
        ;;
        
    clean)
        echo -e "${YELLOW}🧹 Cleaning up...${NC}"
        docker-compose down -v --remove-orphans
        echo ""
        echo -e "${YELLOW}Removing images...${NC}"
        docker images | grep bob-langgraph-agent | awk '{print $3}' | xargs -r docker rmi -f
        echo -e "${GREEN}✅ Cleanup complete${NC}"
        ;;
        
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  up, start    - Start the services (default)"
        echo "  down, stop   - Stop the services"
        echo "  restart      - Restart the services"
        echo "  logs         - View service logs"
        echo "  build        - Build the Docker image"
        echo "  rebuild      - Rebuild the Docker image (no cache)"
        echo "  status       - Show service status"
        echo "  clean        - Stop services and remove containers/images"
        exit 1
        ;;
esac
