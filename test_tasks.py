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
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the existing Celery app and tasks
from workers import (
    celery, 
    generate_user_export, 
    ensure_context,
    log_task_status,
    get_flask_app
)

def check_task_result(task, timeout=30):
    """Monitor task execution and return result"""
    logger.info(f"Monitoring task: {task.id}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if task.ready():
            if task.successful():
                logger.info(f"Task completed: {task.result}")
                return True
            else:
                logger.error(f"Task failed: {task.result}")
                if isinstance(task.result, Exception):
                    logger.error(f"Error: {str(task.result)}")
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

@celery.task(name='tasks.test_daily_reminders')
@ensure_context
@log_task_status("test_daily_reminders")
def test_daily_reminders():
    """Test daily reminders task"""
    try:
        logger.info("Starting daily reminders test")
        from models import User, Role
        from extensions import mail
        logger.info("Imports successful")
        
        # Get users to test with
        users = User.query.join(User.roles).filter(Role.name == 'user').limit(3).all()
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

@celery.task(name='tasks.test_monthly_reports')
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

def test_tasks():
    """Run all task tests"""
    logger.info("Starting task tests...")
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
    
    # Test exports
    print("\nTesting user export...")
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
    
    sys.exit(test_tasks())