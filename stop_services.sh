#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

# Function to check if a process is running
check_process() {
    pgrep -f "$1" >/dev/null 2>&1
}

# Function to stop a service
stop_service() {
    service_name=$1
    process_pattern=$2
    
    echo -e "Stopping $service_name..."
    if check_process "$process_pattern"; then
        pkill -f "$process_pattern"
        # Wait for the process to stop
        for i in {1..5}; do
            if ! check_process "$process_pattern"; then
                echo -e "${GREEN}[OK]${NC} $service_name stopped"
                return 0
            fi
            sleep 1
        done
        # Force kill if still running
        if check_process "$process_pattern"; then
            pkill -9 -f "$process_pattern"
            echo -e "${YELLOW}[WARNING]${NC} $service_name force stopped"
        fi
    else
        echo -e "${YELLOW}[INFO]${NC} $service_name was not running"
    fi
}

echo -e "${YELLOW}Stopping Quiz Master services...${NC}"

# Stop Flask application
stop_service "Flask application" "flask run"

# Stop Celery workers
stop_service "Celery worker" "celery.*worker"

# Stop Celery beat
stop_service "Celery beat" "celery.*beat"

# Stop MailHog
stop_service "MailHog" "mailhog"

# Stop Redis server
stop_service "Redis server" "redis-server"

# Verify all processes are stopped
if pgrep -f "redis-server|mailhog|celery|flask" > /dev/null; then
    echo -e "\n${RED}Warning: Some processes are still running${NC}"
    echo "Running processes:"
    ps aux | grep -E "redis-server|mailhog|celery|flask" | grep -v grep
    exit 1
else
    echo -e "\n${GREEN}All services stopped successfully!${NC}"
fi