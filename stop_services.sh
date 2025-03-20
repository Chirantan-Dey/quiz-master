#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

echo -e "${YELLOW}Stopping Quiz Master services...${NC}"

# Stop Flask application
pkill -f "flask run"
echo -e "${GREEN}[OK]${NC} Stopped Flask application"

# Stop Celery workers
pkill -f "celery worker"
echo -e "${GREEN}[OK]${NC} Stopped Celery workers"

# Stop Celery beat
pkill -f "celery beat"
echo -e "${GREEN}[OK]${NC} Stopped Celery beat"

# Stop MailHog
pkill -f "mailhog"
echo -e "${GREEN}[OK]${NC} Stopped MailHog"

# Stop Redis server
pkill -f "redis-server"
echo -e "${GREEN}[OK]${NC} Stopped Redis server"

# Wait a moment to ensure all processes are stopped
sleep 2

# Verify all processes are stopped
if pgrep -f "redis-server|mailhog|celery|flask" > /dev/null; then
    echo -e "${RED}Some processes are still running. You may need to stop them manually.${NC}"
    exit 1
else
    echo -e "\n${GREEN}All services stopped successfully!${NC}"
fi