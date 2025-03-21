from celery import Celery
from datetime import datetime, timedelta
from flask_mail import Message
import pytz
from functools import wraps
import traceback
import os
import sys
import io
from flask_excel import make_response_from_array, init_excel
import time

# Ensure app directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Celery instance without direct app dependency
celery = Celery('quiz_master')

# Default configuration
class Config:
    CELERY_BROKER_URL = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
    CELERY_TIMEZONE = 'Asia/Kolkata'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TASK_IGNORE_RESULT = False

# Update Celery config
celery.conf.update(
    broker_url=Config.CELERY_BROKER_URL,
    result_backend=Config.CELERY_RESULT_BACKEND,
    timezone=Config.CELERY_TIMEZONE,
    task_serializer=Config.CELERY_TASK_SERIALIZER,
    accept_content=Config.CELERY_ACCEPT_CONTENT,
    result_serializer=Config.CELERY_RESULT_SERIALIZER,
    task_ignore_result=Config.CELERY_TASK_IGNORE_RESULT
)

def get_flask_app():
    """Get Flask app instance"""
    try:
        print("Creating Flask app...")  # Debug log
        from app import create_app
        flask_app = create_app()
        print("Flask app created successfully")  # Debug log
        # Initialize flask-excel with the app
        init_excel(flask_app)
        return flask_app
    except Exception as e:
        print(f"Error creating Flask app: {str(e)}")  # Debug log
        print(f"Python path: {sys.path}")  # Debug log
        raise

def ensure_context(f):
    """Ensure function runs within Flask app context"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            flask_app = get_flask_app()
            with flask_app.app_context():
                print(f"Executing task with app context: {f.__name__}")  # Debug log
                return f(*args, **kwargs)
        except Exception as e:
            print(f"Context error in {f.__name__}: {str(e)}")  # Debug log
            raise
    return wrapper

def log_task_status(name):
    """Decorator to log task status"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            task_id = celery.current_task.request.id if celery.current_task else 'NO-ID'
            print(f"Task {name} [{task_id}] started")  # Debug log
            try:
                result = f(*args, **kwargs)
                print(f"Task {name} [{task_id}] completed successfully")  # Debug log
                return result
            except Exception as e:
                error_msg = f"Task {name} [{task_id}] failed: {str(e)}\nTraceback: {traceback.format_exc()}"
                print(error_msg)  # Debug log
                raise
        return wrapper
    return decorator

def check_task_result(task, timeout=30):
    """Monitor task execution and return result"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if task.ready():
            if task.successful():
                print(f"Task completed: {task.result}")
                return True
            else:
                print(f"Task failed: {task.result}")
                return False
        time.sleep(1)
    print("Task timed out")
    return False

def check_mailhog():
    """Check MailHog for recently sent emails"""
    import requests
    response = requests.get('http://localhost:8025/api/v2/messages')
    if response.ok:
        messages = response.json()
        print(f"\nFound {messages.get('count', 0)} messages in MailHog")
        for msg in messages.get('items', []):
            print(f"From: {msg.get('From', {}).get('Mailbox')}@{msg.get('From', {}).get('Domain')}")
            print(f"Subject: {msg.get('Content', {}).get('Headers', {}).get('Subject', [''])[0]}")
    return response.ok

@celery.task(ignore_result=False)
@ensure_context
@log_task_status("test_daily_reminders")
def test_daily_reminders():
    """Test daily reminders task"""
    from models import User, Quiz, Scores, Role
    from extensions import mail
    from flask import current_app
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    yesterday = now - timedelta(days=1)
    
    # Find inactive users (excluding admins)
    inactive_users = User.query.join(User.roles).filter(
        ~User.scores.any(Scores.time_stamp_of_attempt > yesterday),
        Role.name == 'user'
    ).all()
    
    # Find new quizzes from last 24 hours
    new_quizzes = Quiz.query.filter(
        Quiz.date_of_quiz > yesterday,
        Quiz.date_of_quiz <= now
    ).all()
    
    for user in inactive_users:
        message = Message(
            'Quiz Master - Daily Update (Test)',
            sender='quiz-master@example.com',
            recipients=[user.email]
        )
        message.html = f"""
        <h2>Test Daily Update</h2>
        <p>Hello {user.full_name or user.email},</p>
        <p>This is a test of the daily reminder system.</p>
        """
        mail.send(message)
    
    return f"Test reminders sent to {len(inactive_users)} users"

@celery.task(ignore_result=False)
@ensure_context
@log_task_status("test_monthly_reports")
def test_monthly_reports():
    """Test monthly reports task"""
    from models import User, Scores
    from extensions import mail
    import charts
    from flask import current_app
    
    users = User.query.all()
    sent_count = 0
    
    for user in users:
        message = Message(
            'Test Monthly Activity Report',
            sender='quiz-master@example.com',
            recipients=[user.email]
        )
        message.html = f"""
        <h1>Test Monthly Activity Report</h1>
        <p>Hello {user.full_name or user.email},</p>
        <p>This is a test of the monthly report system.</p>
        """
        mail.send(message)
        sent_count += 1
    
    return f"Test monthly reports sent to {sent_count} users"

def test_tasks():
    """Run all task tests"""
    print("Starting task tests...")
    print("=" * 50)
    
    results = {}
    
    # Test daily reminders
    print("\nTesting daily reminders...")
    task = test_daily_reminders.delay()
    results["Daily Reminders"] = check_task_result(task)
    
    # Test monthly reports
    print("\nTesting monthly reports...")
    task = test_monthly_reports.delay()
    results["Monthly Reports"] = check_task_result(task)
    
    # Test exports (using original task)
    print("\nTesting user export...")
    from workers import generate_user_export
    task = generate_user_export.delay('admin@iitm.ac.in')
    results["User Export"] = check_task_result(task)
    
    # Verify emails were sent
    check_mailhog()
    
    # Print results
    print("\nTest Results:")
    print("=" * 50)
    for task, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        color = "\033[92m" if passed else "\033[91m"
        print(f"{color}{task}: {status}\033[0m")
    
    all_passed = all(results.values())
    print("=" * 50)
    if all_passed:
        print("\033[92mAll tasks completed successfully!\033[0m")
        return 0
    else:
        print("\033[91mSome tasks failed. Check the logs above for details.\033[0m")
        return 1

if __name__ == "__main__":
    sys.exit(test_tasks())