#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        echo "Please install $1 and try again"
        exit 1
    fi
}

# Function to check if a process is running
is_running() {
    if [ -z "$1" ]; then
        return 1
    fi
    if kill -0 "$1" 2>/dev/null; then
        return 0
    fi
    return 1
}

# Function to check service health
check_health() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1

    echo -n "Waiting for $service to start"
    while ! nc -z localhost "$port" 2>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo -e "\n${RED}Failed to start $service${NC}"
            return 1
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo -e "\n${GREEN}$service is running on port $port${NC}"
    return 0
}

# Function to cleanup background processes and logs
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    # Kill Redis server if we started it
    if [ ! -z "$REDIS_PID" ] && is_running "$REDIS_PID"; then
        echo "Stopping Redis..."
        kill "$REDIS_PID"
    fi
    
    # Kill Celery worker and beat
    if [ ! -z "$CELERY_PID" ] && is_running "$CELERY_PID"; then
        echo "Stopping Celery..."
        kill "$CELERY_PID"
    fi
    
    # Kill Flask application
    if [ ! -z "$FLASK_PID" ] && is_running "$FLASK_PID"; then
        echo "Stopping Flask..."
        kill "$FLASK_PID"
    fi
    
    # Stop MailHog in WSL
    echo "Stopping MailHog in WSL..."
    wsl.exe -e pkill mailhog >/dev/null 2>&1

    # Cleanup old log files (older than 7 days)
    if [ "$CLEAN_LOGS" = "true" ]; then
        echo "Cleaning old log files..."
        find logs -type f -name "*.log" -mtime +7 -exec rm {} \;
    fi
    
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

# Function to setup development environment
setup_dev_env() {
    # Create logs directory if it doesn't exist
    mkdir -p logs

    # Create static/charts directories if they don't exist
    mkdir -p static/charts/admin static/charts/user

    # Create instance directory for SQLite database
    mkdir -p instance

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Parse command line arguments
DEV_MODE=false
CLEAN_LOGS=false
SETUP_ENV=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dev) DEV_MODE=true ;;
        --clean-logs) CLEAN_LOGS=true ;;
        --setup) SETUP_ENV=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Check required commands
echo -e "${YELLOW}Checking dependencies...${NC}"
check_command python3
check_command nc
check_command redis-server
check_command wsl.exe

# Setup environment if requested
if [ "$SETUP_ENV" = "true" ]; then
    echo -e "${YELLOW}Setting up development environment...${NC}"
    setup_dev_env
fi

echo -e "${YELLOW}Starting Quiz Master services...${NC}"

# Start MailHog in WSL
echo "Starting MailHog in WSL..."
wsl.exe -e mailhog >/dev/null 2>&1 &
if ! check_health "MailHog" 1025; then
    echo -e "${RED}Failed to start MailHog in WSL${NC}"
    echo "Please install it using: 'sudo apt-get install mailhog'"
    exit 1
fi

# Check if Redis is already running
if nc -z localhost 6379 2>/dev/null; then
    echo -e "${GREEN}Redis is already running on port 6379${NC}"
    REDIS_EXTERNAL=1
else
    echo "Starting Redis..."
    redis-server --daemonize yes &
    REDIS_PID=$!
    if ! check_health "Redis" 6379; then
        exit 1
    fi
fi

# Start Celery worker with beat
echo "Starting Celery worker and beat..."
if [ "$DEV_MODE" = "true" ]; then
    # Development mode with autoreload
    python3 celery_runner.py --worker --beat --loglevel=debug &
else
    python3 celery_runner.py --worker --beat &
fi
CELERY_PID=$!
sleep 2

# Check if Celery started successfully
if ! is_running "$CELERY_PID"; then
    echo -e "${RED}Failed to start Celery${NC}"
    echo "Please check if all dependencies are installed"
    exit 1
fi

# Start Flask application
echo "Starting Flask application..."
if [ "$DEV_MODE" = "true" ]; then
    # Development mode with debug and auto-reload
    FLASK_ENV=development FLASK_DEBUG=1 python3 app.py &
else
    python3 app.py &
fi
FLASK_PID=$!

# Check if Flask started successfully
if ! check_health "Flask" 5000; then
    exit 1
fi

# Start development tools if in dev mode
if [ "$DEV_MODE" = "true" ]; then
    echo -e "${YELLOW}Starting development tools...${NC}"
    
    # Run code formatting and linting
    echo "Running code formatters..."
    black . || true
    isort . || true
    
    # Run type checking in background
    echo "Starting type checker..."
    mypy . --watch &
fi

echo -e "\n${GREEN}All services are running!${NC}"
echo -e "${YELLOW}Available Services:${NC}"
echo "- MailHog SMTP server: localhost:1025"
echo "- MailHog Web UI: http://localhost:8025"
echo "- Flask application: http://localhost:5000"
if [ "$DEV_MODE" = "true" ]; then
    echo -e "\n${YELLOW}Development Mode:${NC}"
    echo "- Auto-reload enabled"
    echo "- Debug mode enabled"
    echo "- Type checking active"
fi
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?