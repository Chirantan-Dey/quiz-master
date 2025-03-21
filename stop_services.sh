#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

echo -e "${YELLOW}Stopping Quiz Master services...${NC}"

# Function to stop a service
stop_service() {
    service_name=$1
    pattern=$2
    
    echo -ne "Stopping $service_name... "
    
    if pgrep -f "$pattern" > /dev/null; then
        pkill -f "$pattern"
        sleep 2  # Give some time for graceful shutdown
        
        if pgrep -f "$pattern" > /dev/null; then
            # If still running, force kill
            pkill -9 -f "$pattern"
        fi
        
        echo -e "${GREEN}[OK]${NC}"
    else
        echo -e "${YELLOW}[NOT RUNNING]${NC}"
    fi
}

# Stop services in reverse order of startup
stop_service "Flask" "flask run"
stop_service "Celery beat" "celery.*beat"
stop_service "Celery worker" "celery.*worker"
stop_service "MailHog" "mailhog"
stop_service "Redis" "redis-server"

# Final check
running_services=""
for pattern in "flask run" "celery.*beat" "celery.*worker" "mailhog" "redis-server"; do
    if pgrep -f "$pattern" > /dev/null; then
        running_services="$running_services\n  - $pattern"
    fi
done

if [ -n "$running_services" ]; then
    echo -e "\n${RED}Warning: Some services are still running:${NC}$running_services"
    echo -e "You may need to stop them manually or use: sudo pkill -9 -f '<pattern>'"
else
    echo -e "\n${GREEN}All Quiz Master services stopped successfully!${NC}"
fi