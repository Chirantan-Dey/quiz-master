# Celery Implementation Improvements

## Current Issues

1. Missing Proper Flask Context Integration
- Current implementation uses raw Celery initialization
- Missing proper Flask application context handling in tasks

2. Task Decorators
- Using `@celery.task` instead of more flexible `@shared_task`
- Could lead to issues with multiple Celery instances

3. Configuration Structure
- Celery config mixed in workers.py
- Could be better organized in a dedicated config module

## Proposed Changes

1. Create `config.py`:
```python
from celery import Celery, Task
from flask import Flask

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
```

2. Update `app.py`:
```python
# Add to create_app()
app.config.from_mapping(
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
    ),
)
celery_init_app(app)
```

3. Update `workers.py`:
```python
from celery import shared_task
from flask import current_app
from extensions import mail
# ... other imports ...

@shared_task(ignore_result=False)
def send_daily_reminders():
    """Send daily reminders to inactive users and notify about new quizzes"""
    # ... existing implementation ...

@shared_task(ignore_result=False)
def send_monthly_reports():
    """Generate and send monthly activity reports"""
    # ... existing implementation ...

@shared_task(ignore_result=False)
def generate_user_export(admin_email):
    """Generate CSV export using flask-excel"""
    # ... existing implementation ...
```

## Benefits

1. Better Flask Integration
- Tasks always run within Flask application context
- Access to Flask configurations and extensions

2. Improved Modularity
- Clear separation of configuration and task implementation
- Better maintainability and testing

3. Enhanced Factory Pattern Support
- Works better with multiple Flask instances
- More flexible for testing scenarios

## Implementation Steps

1. Create `config.py` with Celery configuration
2. Update Celery configuration in `app.py`
3. Modify task decorators in `workers.py`
4. Update service scripts to use new configuration

## Testing Changes

1. Verify task execution
2. Check Flask context availability
3. Validate configuration loading
4. Test multiple worker scenarios

## Notes

- Keep existing task implementations as they are working well
- Only change the configuration and context handling
- Ensure backward compatibility during transition