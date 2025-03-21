import requests
import time
from celery.result import AsyncResult
from workers import celery

def check_task_status(task_id):
    """Check status of a Celery task"""
    result = AsyncResult(task_id, app=celery)
    print(f"\nTask ID: {task_id}")
    print(f"Task status: {result.status}")
    
    if result.ready():
        if result.successful():
            print(f"Task result: {result.result}")
        else:
            print(f"Task failed: {result.result}")
            if isinstance(result.result, Exception):
                print(f"Error: {str(result.result)}")
                print(f"Traceback: {result.traceback}")
    return result

def test_export():
    """Test export functionality"""
    print("Testing export functionality...")
    
    # Login as admin to get token
    login_data = {
        'email': 'admin@iitm.ac.in',
        'password': 'pass'
    }
    
    print("\n1. Logging in...")
    # Get auth token
    response = requests.post('http://localhost:5000/', json=login_data)
    if not response.ok:
        print(f"Login failed: {response.text}")
        return
    print("Login successful")
        
    token = response.json()['access_token']
    headers = {'Authentication-Token': token}
    
    print("\n2. Triggering export...")
    # Test export endpoint
    response = requests.post(
        'http://localhost:5000/api/export/users',
        headers=headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    if response.ok:
        task_id = response.json().get('task_id')
        if task_id:
            print("\n3. Monitoring task status...")
            # Monitor the task for up to 30 seconds
            start_time = time.time()
            while time.time() - start_time < 30:
                result = check_task_status(task_id)
                if result.ready():
                    break
                time.sleep(1)
            print("\nTask monitoring completed")
        else:
            print("No task ID in response")
    else:
        print(f"Export request failed: {response.text}")
    
    print("\n4. Checking MailHog for emails...")
    mailhog_response = requests.get('http://localhost:8025/api/v2/messages')
    if mailhog_response.ok:
        messages = mailhog_response.json()
        print(f"Found {messages.get('count', 0)} messages")
        for msg in messages.get('items', []):
            print(f"\nEmail from: {msg.get('From', {}).get('Mailbox')}@{msg.get('From', {}).get('Domain')}")
            print(f"To: {[f'{to.get('Mailbox')}@{to.get('Domain')}' for to in msg.get('To', [])]}")
            print(f"Subject: {msg.get('Content', {}).get('Headers', {}).get('Subject', [''])[0]}")
    else:
        print("Failed to check MailHog")

if __name__ == "__main__":
    test_export()