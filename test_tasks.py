from celery import Celery
from datetime import datetime, timedelta
from flask_mail import Message
import pytz
from functools import wraps
import traceback
import os
import sys
import io
from flask_excel import init_excel
import time

# Import only the Celery configuration
from workers import Config

# Create new Celery app for tests
celery = Celery('quiz_master_test')

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
    print(f"Monitoring task: {task.id}")
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
        print(".", end="", flush=True)
    print("\nTask timed out")
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
            print(f"To: {[f'{to.get('Mailbox')}@{to.get('Domain')}' for to in msg.get('To', [])]}")
            print(f"Subject: {msg.get('Content', {}).get('Headers', {}).get('Subject', [''])[0]}")
    return response.ok

# Register tasks with explicit names
@celery.task(name='test_daily_reminders')
@ensure_context
@log_task_status("test_daily_reminders")
def test_daily_reminders():
    """Test daily reminders task"""
    try:
        from models import User, Role
        from extensions import mail
        
        # Get users to test with
        users = User.query.join(User.roles).filter(Role.name == 'user').limit(3).all()
        sent_count = 0
        
        for user in users:
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
            sent_count += 1
            print(f"Test reminder sent to {user.email}")
        
        return f"Test reminders sent to {sent_count} users"
    except Exception as e:
        print(f"Error in test_daily_reminders: {str(e)}")
        raise

@celery.task(name='test_monthly_reports')
@ensure_context
@log_task_status("test_monthly_reports")
def test_monthly_reports():
    """Test monthly reports task"""
    try:
        from models import User
        from extensions import mail
        
        # Get users to test with
        users = User.query.limit(3).all()
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
            print(f"Test monthly report sent to {user.email}")
        
        return f"Test monthly reports sent to {sent_count} users"
    except Exception as e:
        print(f"Error in test_monthly_reports: {str(e)}")
        raise

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
    
    # Test exports (using original task from workers.py)
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
    # Ensure the app directory is in the Python path
    app_dir = os.path.dirname(os.path.abspath(__file__))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
    sys.exit(test_tasks())