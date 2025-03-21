# Celery Startup Guide

## Issue Identified
The integration test shows Celery worker is not running while other services (Redis, MailHog, API) are working correctly.

## Correct Startup Sequence

1. Check Redis Configuration:
```bash
# Verify Redis is running and accessible
redis-cli ping  # Should return PONG
redis-cli -n 1 ping  # Check DB 1 (Celery broker)
```

2. Start Celery Worker:
```bash
# Start worker with appropriate log level for debugging
celery -A workers.celery worker --loglevel=debug
```

3. Start Celery Beat (in separate terminal):
```bash
celery -A workers.celery beat --loglevel=debug
```

## Celery Worker Status Check

To verify worker status:
```bash
# Check worker status
celery -A workers.celery status

# List active tasks
celery -A workers.celery inspect active
```

## Common Issues and Solutions

1. Worker Not Starting:
- Verify Redis is running
- Check Redis connection strings
- Ensure app context is available
- Check for port conflicts

2. Task Queue Issues:
- Clear Redis task queue:
```bash
redis-cli -n 1 FLUSHDB
```
- Restart worker with purge:
```bash
celery -A workers.celery worker --loglevel=debug --purge
```

3. Beat Schedule Issues:
- Remove old schedule file:
```bash
rm celerybeat-schedule
```
- Restart beat process

## Monitoring Setup

1. Real-time Task Monitoring:
```bash
# Watch task events
celery -A workers.celery events
```

2. Log Review:
```bash
# Tail worker logs
tail -f celery.log
```

## Service Dependencies

Order of startup should be:
1. Redis server
2. MailHog
3. Celery worker
4. Celery beat
5. Flask application

## Testing Steps

1. Start each service separately to identify issues:
```bash
# 1. Start Redis
redis-server

# 2. Start MailHog
mailhog

# 3. Start Celery worker
celery -A workers.celery worker --loglevel=debug

# 4. Start Celery beat
celery -A workers.celery beat --loglevel=debug

# 5. Start Flask
flask run
```

2. Verify each service:
```bash
# Test Redis
redis-cli ping

# Test Celery
celery -A workers.celery status

# Test Flask
curl http://localhost:5000/health  # If health endpoint exists
```

## Update to start_services.sh

Consider updating start_services.sh to:
1. Add more verbose logging
2. Include status checks
3. Add retry mechanism for service startup
4. Include proper error handling

Example improvements:
```bash
# Start Celery worker with retries
MAX_RETRIES=3
retry_count=0
while [ $retry_count -lt $MAX_RETRIES ]; do
    echo "Starting Celery worker (attempt $((retry_count + 1)))..."
    celery -A workers.celery worker --loglevel=debug &
    sleep 5
    if celery -A workers.celery status >/dev/null 2>&1; then
        echo "Celery worker started successfully"
        break
    fi
    ((retry_count++))
done

if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "Failed to start Celery worker after $MAX_RETRIES attempts"
    exit 1
fi
```

## Next Steps

1. Update service scripts with better error handling
2. Add proper health checks for each service
3. Implement proper logging configuration
4. Add monitoring endpoints

Remember to always check logs (`--loglevel=debug`) when troubleshooting Celery worker issues.