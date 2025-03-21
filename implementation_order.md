# Implementation Order for Celery Integration

## Step 1: Update app.py

1. Add required imports:
```python
from celery import Celery, Task
from celery.schedules import crontab
```

2. Add FlaskTask class and Celery configuration in create_app():
```python
def create_app():
    app = Flask(__name__)
    
    # ... existing configurations ...

    # Add Celery configuration
    app.config.update(
        CELERY=dict(
            broker_url="redis://localhost:6379/1",
            result_backend="redis://localhost:6379/1",
            task_ignore_result=True,
            timezone='Asia/Kolkata',
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            beat_schedule={
                'evening-reminder': {
                    'task': 'workers.send_daily_reminders',
                    'schedule': crontab(hour=18, minute=0)
                },
                'monthly-report': {
                    'task': 'workers.send_monthly_reports',
                    'schedule': crontab(0, 0, day_of_month='1')
                }
            }
        )
    )

    # ... rest of configuration ...

    # Initialize Celery
    celery_app = Celery(app.name)
    celery_app.config_from_object(app.config["CELERY"])
    app.extensions["celery"] = celery_app

    return app
```

## Step 2: Update workers.py

1. Remove Celery initialization code:
```python
# Remove these lines
celery = Celery('quiz_master')
celery.conf.update(...)
```

2. Update task decorators:
```python
from celery import shared_task

@shared_task(ignore_result=False)
def send_daily_reminders():
    # existing implementation...

@shared_task(ignore_result=False)
def send_monthly_reports():
    # existing implementation...

@shared_task(ignore_result=False)
def generate_user_export(admin_email):
    # existing implementation...
```

## Step 3: Service Script Updates

No changes needed to start_services.sh and stop_services.sh as they already handle:
- Redis server
- Celery worker
- Celery beat
- Flask application

## Step 4: Testing Procedure

1. Start services:
```bash
./start_services.sh
```

2. Test functionality:
- Verify daily reminder scheduling
- Test monthly report generation
- Check user data export
- Validate email sending

3. Run integration tests:
```bash
python test_integrations.py
```

## Verification Steps

1. Celery Worker Status:
```bash
celery -A workers status
```

2. Check Redis Connections:
```bash
redis-cli ping
```

3. Monitor Task Execution:
```bash
celery -A workers events
```

## Success Criteria

1. All tasks execute properly
2. Flask context is available in tasks
3. Scheduled tasks run at correct times
4. Email notifications work
5. Integration tests pass
6. No disruption to existing functionality

## Rollback Plan

If issues arise:
1. Keep copy of original files
2. Document any database changes
3. Maintain backup of configurations
4. Test reverting procedures

## Notes

- Implementation preserves existing functionality
- No database schema changes required
- Configuration remains centralized in app.py
- Tasks maintain current behavior
- Flask context handling is improved
- Celery integration follows best practices