#!/bin/bash
# Run all microservices concurrently
# Usage: ./run_all_services.sh

echo "Starting all microservices..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Activating .venv..."
    source .venv/bin/activate
fi

# Start services in background
echo -e "${GREEN}Starting Gateway (Port 8000)...${NC}"
uvicorn services.gateway.app.main:app --port 8000 &
GATEWAY_PID=$!

echo -e "${GREEN}Starting User Service (Port 8001)...${NC}"
uvicorn services.user_service.app.main:app --port 8001 &
USER_PID=$!

echo -e "${GREEN}Starting Submission Service (Port 8002)...${NC}"
uvicorn services.submission_service.app.main:app --port 8002 &
SUBMISSION_PID=$!

echo -e "${GREEN}Starting Plagiarism Service (Port 8003)...${NC}"
uvicorn services.plagiarism_service.app.main:app --port 8003 &
PLAGIARISM_PID=$!

echo -e "${GREEN}Starting Analytics Service (Port 8004)...${NC}"
uvicorn services.analytics_service.app.main:app --port 8004 &
ANALYTICS_PID=$!

echo -e "${GREEN}Starting Notification Service (Port 8005)...${NC}"
uvicorn services.notification_service.app.main:app --port 8005 &
NOTIFICATION_PID=$!

echo ""
echo -e "${GREEN}All services started!${NC}"
echo ""
echo "Service URLs:"
echo "  - Gateway:           http://localhost:8000"
echo "  - User Service:      http://localhost:8001/docs"
echo "  - Submission:        http://localhost:8002/docs"
echo "  - Plagiarism:        http://localhost:8003/docs"
echo "  - Analytics:         http://localhost:8004/docs"
echo "  - Notification:      http://localhost:8005/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${RED}Stopping all services...${NC}"
    kill $GATEWAY_PID $USER_PID $SUBMISSION_PID $PLAGIARISM_PID $ANALYTICS_PID $NOTIFICATION_PID 2>/dev/null
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

# Set trap to catch Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for all background processes
wait
