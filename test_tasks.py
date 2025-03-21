import os
import sys
from datetime import datetime, timedelta
import time
from celery.result import AsyncResult
from workers import (
    celery, 
    send_daily_reminders,
    send_monthly_reports,
    generate_user_export
)

def check_task_status(task_id, timeout=30):
    """Monitor task status with timeout"""
    print(f"\nMonitoring task: {task_id}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = AsyncResult(task_id, app=celery)
        print(f"Status: {result.status}")
        
        if result.ready():
            if result.successful():
                print(f"Task completed: {result.result}")
            else:
                print(f"Task failed: {result.result}")
                if isinstance(result.result, Exception):
                    print(f"Error: {str(result.result)}")
                    print(f"Traceback: {result.traceback}")
            return result
        time.sleep(1)
    
    print("Task monitoring timed out")
    return None

def check_mailhog():
    """Check MailHog for recently received emails"""
    import requests
    print("\nChecking MailHog for emails...")
    response = requests.get('http://localhost:8025/api/v2/messages')
    if response.ok:
        messages = response.json()
        print(f"Found {messages.get('count', 0)} messages")
        for msg in messages.get('items', []):
            print(f"\nEmail from: {msg.get('From', {}).get('Mailbox')}@{msg.get('From', {}).get('Domain')}")
            print(f"To: {[f'{to.get('Mailbox')}@{to.get('Domain')}' for to in msg.get('To', [])]}")
            print(f"Subject: {msg.get('Content', {}).get('Headers', {}).get('Subject', [''])[0]}")
            
            # Check for attachments
            data = msg.get('Raw', {}).get('Data', '')
            has_csv = 'Content-Type: text/csv' in data
            if has_csv:
                print("Has CSV attachment: Yes")

def test_daily_reminders():
    """Test daily reminders task"""
    print("\nTesting daily reminders task...")
    task = send_daily_reminders.delay()
    result = check_task_status(task.id)
    if result and result.successful():
        check_mailhog()
    return result.successful() if result else False

def test_monthly_reports():
    """Test monthly reports task"""
    print("\nTesting monthly reports task...")
    task = send_monthly_reports.delay()
    result = check_task_status(task.id)
    if result and result.successful():
        check_mailhog()
    return result.successful() if result else False

def test_user_export():
    """Test user export task"""
    print("\nTesting user export task...")
    admin_email = 'admin@iitm.ac.in'
    task = generate_user_export.delay(admin_email)
    result = check_task_status(task.id)
    if result and result.successful():
        check_mailhog()
    return result.successful() if result else False

def run_all_tests():
    """Run all task tests"""
    print("Starting Celery task tests...")
    print("=" * 50)
    
    results = {
        "Daily Reminders": test_daily_reminders(),
        "Monthly Reports": test_monthly_reports(),
        "User Export": test_user_export()
    }
    
    print("\nTest Summary:")
    print("=" * 50)
    all_passed = True
    for task, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        color = "\033[92m" if passed else "\033[91m"  # Green for pass, Red for fail
        print(f"{color}{task}: {status}\033[0m")
        all_passed = all_passed and passed
    
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
    
    sys.exit(run_all_tests())