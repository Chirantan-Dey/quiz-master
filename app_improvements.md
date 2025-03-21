# Improving app.py with Celery Configuration

## Current Structure
Currently in app.py we have:
- Flask app creation
- Database configuration
- Cache configuration
- Mail configuration
- Security setup
- View and API initialization

## Proposed Changes to app.py

1. Add FlaskTask class inside create_app():
```python
def create_app():
    app = Flask(__name__)

    # Add FlaskTask class definition
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)
```

2. Add Celery Configuration:
```python
    # Add after other configurations
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
```

3. Add Celery Initialization:
```python
    # Initialize Celery with Flask app context
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
```

## Updates to workers.py

1. Change task decorators:
```python
from celery import shared_task

@shared_task(ignore_result=False)
def send_daily_reminders():
    # existing implementation
```

## Benefits

1. Simpler Architecture
- All configurations in one place
- Easier to maintain and understand
- No need for separate config.py

2. Better Organization
- App configuration stays centralized
- Clear initialization flow
- Less file switching for configuration changes

3. Improved Context Handling
- Tasks automatically get Flask context
- Better integration with Flask extensions
- Consistent error handling

## Implementation Notes

1. Keep existing task implementations untouched
2. Only update the configuration and decorator parts
3. Ensure backward compatibility
4. Maintain existing security settings

## Testing Considerations

1. Verify task execution with new configuration
2. Check Flask context in tasks
3. Validate Redis connectivity
4. Test scheduled tasks

This approach maintains the simplicity of the current setup while incorporating the best practices from the example implementation.