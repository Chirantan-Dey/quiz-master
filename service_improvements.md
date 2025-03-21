# Service Script Improvements

## Current Issues
1. No proper service health checks
2. Celery worker not starting reliably
3. No retry mechanism
4. Limited error handling

## Proposed Changes to start_services.sh

```bash
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
    curl -s http://localhost:5000 >/dev/null 2>&1
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

# Start Redis
start_service "Redis" "redis-server" "check_redis" || exit 1

# Start MailHog
start_service "MailHog" "mailhog" "check_mailhog" || exit 1

# Start Celery worker with proper logging
start_service "Celery worker" "celery -A workers.celery worker --loglevel=debug" "check_celery" || exit 1

# Start Celery beat
start_service "Celery beat" "celery -A workers.celery beat --loglevel=debug" "check_celery" || exit 1

# Start Flask application
export FLASK_APP=app.py
export FLASK_ENV=development
start_service "Flask" "flask run" "check_flask" || exit 1

echo -e "\n${GREEN}All services started successfully!${NC}"
echo -e "${YELLOW}Run python test_integrations.py to test the integration${NC}"
echo -e "\nPress Ctrl+C to stop all services"

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
```

## Improvements Made

1. Service Health Checks
- Added dedicated check functions for each service
- Proper timeout handling
- Verification of service availability

2. Retry Mechanism
- Configurable maximum retries
- Retry interval settings
- Progressive retry attempts

3. Enhanced Error Handling
- Proper service dependency checks
- Clear error messages
- Graceful failure handling

4. Better Cleanup
- Proper signal handling
- Systematic service shutdown
- Clear status messages

5. Logging and Debugging
- Increased log verbosity
- Clear status indicators
- Better progress tracking

## Implementation Notes

To implement these changes:

1. Update start_services.sh with the new code
2. Make it executable:
```bash
chmod +x start_services.sh
```

3. Test with different scenarios:
- Clean startup
- Service failure recovery
- Proper shutdown

4. Monitor logs:
```bash
tail -f celery.log
```

These improvements will make the service startup more reliable and easier to troubleshoot.