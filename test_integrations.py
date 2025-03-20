import os
import sys
import redis
import requests
from datetime import datetime, timedelta
from flask import Flask
from flask_mail import Message
import json
import time
import psutil
import socket

def check_process_running(process_name):
    """Check if a process is running"""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if process_name in str(proc.info).lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def test_redis_connection():
    """Test Redis connections for both cache and Celery"""
    print("\nTesting Redis connections...")
    
    try:
        # First check if Redis server is running
        if not check_process_running('redis-server'):
            print("✗ Redis server is not running")
            return False

        # Test Cache Redis (DB 0)
        cache_redis = redis.Redis(host='localhost', port=6379, db=0)
        cache_redis.set('test_key', 'test_value')
        test_value = cache_redis.get('test_key')
        if test_value.decode('utf-8') == 'test_value':
            print("✓ Cache Redis (DB 0) connection successful")
        else:
            print("✗ Cache Redis (DB 0) test failed")
            return False
        
        # Test Celery Redis (DB 1)
        celery_redis = redis.Redis(host='localhost', port=6379, db=1)
        celery_redis.set('celery_test', 'test_value')
        test_value = celery_redis.get('celery_test')
        if test_value.decode('utf-8') == 'test_value':
            print("✓ Celery Redis (DB 1) connection successful")
        else:
            print("✗ Celery Redis (DB 1) test failed")
            return False
        
        return True
        
    except redis.ConnectionError as e:
        print(f"✗ Redis connection failed: {str(e)}")
        print("Make sure Redis server is running on localhost:6379")
        return False

def test_mailhog_connection():
    """Test MailHog SMTP connection"""
    print("\nTesting MailHog connection...")
    
    try:
        # First check if MailHog is running
        if not check_process_running('mailhog'):
            print("✗ MailHog is not running")
            return False

        # Create test Flask app
        app = Flask(__name__)
        app.config.update(
            MAIL_SERVER='localhost',
            MAIL_PORT=1025,
            MAIL_USE_TLS=False,
            MAIL_USE_SSL=False
        )
        
        from extensions import mail
        mail.init_app(app)
        
        with app.app_context():
            msg = Message(
                'Test Email',
                sender='test@example.com',
                recipients=['admin@example.com']
            )
            msg.body = "This is a test email"
            mail.send(msg)
            
        print("✓ MailHog connection successful")
        
        # Check if email was received via MailHog API
        time.sleep(1)  # Wait for email to be processed
        response = requests.get('http://localhost:8025/api/v2/messages')
        if response.ok and len(response.json()['items']) > 0:
            print("✓ MailHog received test email")
            return True
        else:
            print("✗ MailHog didn't receive test email")
            return False
            
    except Exception as e:
        print(f"✗ MailHog connection failed: {str(e)}")
        print("Make sure MailHog is running (SMTP: 1025, HTTP: 8025)")
        return False

def test_celery_task():
    """Test Celery task execution"""
    print("\nTesting Celery task execution...")
    
    try:
        # Check if Celery worker is running
        if not check_process_running('celery worker'):
            print("✗ Celery worker is not running")
            return False

        from workers import celery, send_daily_reminders
        
        # Start a test task
        task = send_daily_reminders.delay()
        
        # Wait for task completion (max 10 seconds)
        timeout = 10
        start_time = time.time()
        while time.time() - start_time < timeout:
            if task.ready():
                if task.successful():
                    print("✓ Celery task executed successfully")
                    print(f"Task result: {task.result}")
                    return True
                else:
                    print(f"✗ Celery task failed: {task.result}")
                    return False
            time.sleep(0.5)
        else:
            print("✗ Celery task timed out")
            return False
            
    except Exception as e:
        print(f"✗ Celery test failed: {str(e)}")
        print("Make sure Celery worker is running")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\nTesting API endpoints...")
    
    try:
        # Check if Flask app is running
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        if result != 0:
            print("✗ Flask application is not running")
            return False

        # Login as admin to get token
        login_data = {
            'email': 'admin@iitm.ac.in',
            'password': 'pass'
        }
        
        response = requests.post('http://localhost:5000/', json=login_data)
        if not response.ok:
            print("✗ Login failed")
            return False
            
        token = response.json()['access_token']
        headers = {'Authentication-Token': token}
        
        # Test export endpoint
        response = requests.post(
            'http://localhost:5000/api/export/users',
            headers=headers
        )
        
        if response.ok:
            print("✓ Export API endpoint working")
            print(f"Response: {response.json()['message']}")
            return True
        else:
            print(f"✗ Export API failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ API test failed: {str(e)}")
        print("Make sure Flask application is running")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("Starting integration tests...")
    print("=" * 50)
    
    results = {
        "Redis": test_redis_connection(),
        "MailHog": test_mailhog_connection(),
        "Celery": test_celery_task(),
        "API": test_api_endpoints()
    }
    
    print("\nTest Summary:")
    print("=" * 50)
    all_passed = True
    for service, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        color = "\033[92m" if passed else "\033[91m"  # Green for pass, Red for fail
        print(f"{color}{service}: {status}\033[0m")
        all_passed = all_passed and passed
    
    print("=" * 50)
    if all_passed:
        print("\033[92mAll tests passed successfully!\033[0m")
        return 0
    else:
        print("\033[91mSome tests failed. Check the logs above for details.\033[0m")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())