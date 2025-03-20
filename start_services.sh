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

# Function to check if a port is in use
check_port() {
    nc -z localhost $1 >/dev/null 2>&1
}

# Function to print colored status
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} $1"
    else
        echo -e "${RED}[FAILED]${NC} $1"
        exit 1
    fi
}

echo -e "${YELLOW}Starting services for Quiz Master...${NC}"

# Check if Redis is running
if ! check_port 6379; then
    echo "Starting Redis server..."
    redis-server &
    sleep 2
fi
print_status "Redis server"

# Check if MailHog is running
if ! check_port 1025; then
    echo "Starting MailHog..."
    mailhog >/dev/null 2>&1 &
    sleep 2
fi
print_status "MailHog"

# Start Celery worker
echo "Starting Celery worker..."
celery -A workers.celery worker --loglevel=info &
print_status "Celery worker"

# Start Celery beat
echo "Starting Celery beat..."
celery -A workers.celery beat --loglevel=info &
print_status "Celery beat"

# Start Flask application
echo "Starting Flask application..."
export FLASK_APP=app.py
export FLASK_ENV=development
flask run &
print_status "Flask application"

echo -e "\n${GREEN}All services started successfully!${NC}"
echo -e "${YELLOW}Run python test_integrations.py to test the integration${NC}"
echo -e "\nPress Ctrl+C to stop all services"

# Wait for user interrupt
trap 'kill $(jobs -p)' INT
wait