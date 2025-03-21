from celery import Celery
from datetime import datetime, timedelta
from flask_mail import Message
import pytz
from functools import wraps
import traceback
import os
import sys
import io
from flask_excel import init_excel, make_response_from_array
import time
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create new Celery app for tests
test_celery = Celery('test_tasks')

# Configure Celery
test_celery.conf.update(
    broker_url='redis://localhost:6379/1',
    result_backend='redis://localhost:6379/1',
    imports=['test_tasks'],
    task_ignore_result=False,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json'
)

def get_flask_app():
    """Get Flask app instance"""
    try:
        logger.info("Creating Flask app...")
        from app import create_app
        flask_app = create_app()
        logger.info("Flask app created successfully")
        init_excel(flask_app)
        return flask_app
    except Exception as e:
        logger.error(f"Error creating Flask app: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def ensure_context(f):
    """Ensure function runs within Flask app context"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            flask_app = get_flask_app()
            with flask_app.app_context():
                logger.info(f"Executing {f.__name__} within app context")
                return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Context error in {f.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    return wrapper

def log_task_status(name):
    """Decorator to log task status"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            task_id = test_celery.current_task.request.id if test_celery.current_task else 'NO-ID'
            logger.info(f"Task {name} [{task_id}] started")
            try:
                result = f(*args, **kwargs)
                logger.info(f"Task {name} [{task_id}] completed successfully")
                return result
            except Exception as e:
                error_msg = f"Task {name} [{task_id}] failed: {str(e)}\nTraceback: {traceback.format_exc()}"
                logger.error(error_msg)
                raise
        return wrapper
    return decorator

def check_task_result(task, timeout=30):
    """Monitor task execution and return result"""
    logger.info(f"Monitoring task: {task.id}")
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        status = task.status
        if status != last_status:
            logger.info(f"Task status: {status}")
            last_status = status
            
        if task.ready():
            if task.successful():
                result = task.result
                logger.info(f"Task completed: {result}")
                return True
            else:
                error = task.result
                logger.error(f"Task failed: {error}")
                if isinstance(error, Exception):
                    logger.error(f"Error: {str(error)}")
                    logger.error(f"Traceback: {task.traceback}")
                return False
        time.sleep(1)
        print(".", end="", flush=True)
    
    logger.warning("Task timed out")
    return False

def check_mailhog():
    """Check MailHog for recently sent emails"""
    import requests
    logger.info("Checking MailHog for emails")
    response = requests.get('http://localhost:8025/api/v2/messages')
    if response.ok:
        messages = response.json()
        logger.info(f"Found {messages.get('count', 0)} messages in MailHog")
        for msg in messages.get('items', []):
            logger.info(f"From: {msg.get('From', {}).get('Mailbox')}@{msg.get('From', {}).get('Domain')}")
            logger.info(f"To: {[f'{to.get('Mailbox')}@{to.get('Domain')}' for to in msg.get('To', [])]}")
            logger.info(f"Subject: {msg.get('Content', {}).get('Headers', {}).get('Subject', [''])[0]}")
    else:
        logger.error("Failed to check MailHog")
    return response.ok

@test_celery.task(name='test.daily_reminders')
@ensure_context
@log_task_status("test_daily_reminders")
def test_daily_reminders():
    """Test daily reminders task"""
    try:
        logger.info("Starting daily reminders test")
        from models import User
        from extensions import mail
        logger.info("Imports successful")
        
        # Get users to test with
        users = User.query.limit(3).all()
        logger.info(f"Found {len(users)} users for testing")
        sent_count = 0
        
        for user in users:
            logger.info(f"Preparing email for {user.email}")
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
            
            try:
                logger.info(f"Sending email to {user.email}")
                mail.send(message)
                sent_count += 1
                logger.info(f"Email sent to {user.email}")
            except Exception as mail_error:
                logger.error(f"Failed to send email to {user.email}: {str(mail_error)}")
                logger.error(traceback.format_exc())
                raise
        
        result = f"Test reminders sent to {sent_count} users"
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"Error in test_daily_reminders: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@test_celery.task(name='test.monthly_reports')
@ensure_context
@log_task_status("test_monthly_reports")
def test_monthly_reports():
    """Test monthly reports task"""
    try:
        logger.info("Starting monthly reports test")
        from models import User
        from extensions import mail
        logger.info("Imports successful")
        
        # Get users to test with
        users = User.query.limit(3).all()
        logger.info(f"Found {len(users)} users for testing")
        sent_count = 0
        
        for user in users:
            logger.info(f"Preparing report for {user.email}")
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
            
            try:
                logger.info(f"Sending report to {user.email}")
                mail.send(message)
                sent_count += 1
                logger.info(f"Report sent to {user.email}")
            except Exception as mail_error:
                logger.error(f"Failed to send report to {user.email}: {str(mail_error)}")
                logger.error(traceback.format_exc())
                raise
        
        result = f"Test monthly reports sent to {sent_count} users"
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"Error in test_monthly_reports: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@test_celery.task(name='test.user_export')
@ensure_context
@log_task_status("test_user_export")
def test_user_export(admin_email):
    """Test user export task"""
    try:
        logger.info("Starting test export")
        from models import User
        from extensions import mail
        logger.info("Imports successful")
        
        # Get users to test with
        users = User.query.limit(3).all()
        logger.info(f"Found {len(users)} users for testing")
        
        data = [['User ID', 'Name', 'Email', 'Total Quizzes']]
        for user in users:
            data.append([
                user.id,
                user.full_name or 'N/A',
                user.email,
                len(user.scores)
            ])
        
        # Generate CSV
        logger.info("Generating CSV file...")
        excel_file = make_response_from_array(data, "csv")
        
        # Send email
        message = Message(
            'Test User Data Export',
            sender='quiz-master@example.com',
            recipients=[admin_email]
        )
        message.html = f"""
        <h2>Test User Data Export</h2>
        <p>This is a test export.</p>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        message.attach(
            "test_export.csv",
            "text/csv",
            excel_file.get_data()
        )
        
        logger.info(f"Sending export email to {admin_email}")
        mail.send(message)
        
        result = "Test export completed and sent"
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"Error in test_user_export: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def run_test_task(task_func, *args, **kwargs):
    """Run a task and monitor its execution"""
    task = task_func.delay(*args, **kwargs)
    return check_task_result(task)

def test_tasks():
    """Run all task tests"""
    logger.info("Starting task tests...")
    print("Starting task tests...")
    print("=" * 50)
    
    results = {}
    
    # Test daily reminders
    print("\nTesting daily reminders...")
    results["Daily Reminders"] = run_test_task(test_daily_reminders)
    
    # Test monthly reports
    print("\nTesting monthly reports...")
    results["Monthly Reports"] = run_test_task(test_monthly_reports)
    
    # Test exports
    print("\nTesting user export...")
    results["User Export"] = run_test_task(test_user_export, 'admin@iitm.ac.in')
    
    # Verify emails were sent
    check_mailhog()
    
    # Print results
    print("\nTest Results:")
    print("=" * 50)
    for task, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        color = "\033[92m" if passed else "\033[91m"
        print(f"{color}{task}: {status}\033[0m")
        logger.info(f"{task}: {'PASSED' if passed else 'FAILED'}")
    
    all_passed = all(results.values())
    print("=" * 50)
    if all_passed:
        logger.info("All tasks completed successfully!")
        print("\033[92mAll tasks completed successfully!\033[0m")
        return 0
    else:
        logger.error("Some tasks failed")
        print("\033[91mSome tasks failed. Check the logs above for details.\033[0m")
        return 1

if __name__ == "__main__":
    # Ensure the app directory is in the Python path
    app_dir = os.path.dirname(os.path.abspath(__file__))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    logger.info(f"Python path: {sys.path}")
    
    # Start test tasks worker if not already running
    if len(sys.argv) > 1 and sys.argv[1] == 'worker':
        test_celery.worker_main(['worker', '--loglevel=DEBUG'])
    else:
        sys.exit(test_tasks())