#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

# Configuration
MAX_RETRIES=3
RETRY_INTERVAL=5
HEALTH_CHECK_TIMEOUT=30

# Enhanced check functions
check_redis() {
    redis-cli ping >/dev/null 2>&1
}

check_mailhog() {
    nc -z localhost 1025 >/dev/null 2>&1
}

check_celery() {
    celery -A workers.celery status >/dev/null 2>&1
}

check_flask() {
    curl -s http://localhost:5000/health >/dev/null 2>&1
}

# Service startup with retries
start_service() {
    service_name=$1
    start_command=$2
    check_function=$3
    
    echo -e "${YELLOW}Starting $service_name...${NC}"
    
    retry_count=0
    while [ $retry_count -lt $MAX_RETRIES ]; do
        eval "$start_command" &
        
        # Wait for service to start
        waited=0
        while [ $waited -lt $HEALTH_CHECK_TIMEOUT ]; do
            if eval "$check_function"; then
                echo -e "${GREEN}[OK]${NC} $service_name started successfully"
                return 0
            fi
            sleep 1
            ((waited++))
        done
        
        ((retry_count++))
        if [ $retry_count -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}Retrying $service_name start (attempt $((retry_count + 1))/${MAX_RETRIES})${NC}"
            pkill -f "$service_name"
            sleep $RETRY_INTERVAL
        fi
    done
    
    echo -e "${RED}[FAILED]${NC} Could not start $service_name after $MAX_RETRIES attempts"
    return 1
}

# Main script
echo -e "${YELLOW}Starting services for Quiz Master...${NC}"

# Ensure virtual environment is activated if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Start Redis
start_service "Redis" "redis-server" "check_redis" || exit 1

# Start MailHog
start_service "MailHog" "mailhog" "check_mailhog" || exit 1

# Start Celery worker with proper logging
start_service "Celery worker" "celery -A workers.celery worker --loglevel=info" "check_celery" || exit 1

# Start Celery beat for scheduled tasks
start_service "Celery beat" "celery -A workers.celery beat --loglevel=info" "check_celery" || exit 1

# Start Flask application
export FLASK_APP=app.py
export FLASK_DEBUG=1
start_service "Flask" "python -m flask run" "check_flask" || exit 1

echo -e "\n${GREEN}All services started successfully!${NC}"
echo -e "${YELLOW}The Quiz Master application is now running:${NC}"
echo -e "  - Web interface: http://localhost:5000"
echo -e "  - MailHog interface: http://localhost:8025"
echo -e "\nPress Ctrl+C to stop all services\n"

# Improved cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping all services...${NC}"
    pkill -f "redis-server"
    pkill -f "mailhog"
    pkill -f "celery"
    pkill -f "flask"
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

trap cleanup INT TERM

# Wait for interrupt
wait