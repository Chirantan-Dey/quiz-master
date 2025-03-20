# Testing Guide for Quiz Master Background Tasks

## Prerequisites

1. Redis server installed
2. MailHog installed
3. Python 3.x with pip

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make service scripts executable:
```bash
chmod +x start_services.sh stop_services.sh
```

## Starting Services

To start all required services:
```bash
./start_services.sh
```

This will automatically start:
- Redis server
- MailHog (SMTP on port 1025, Web UI on port 8025)
- Celery worker
- Celery beat scheduler
- Flask application

## Running Tests

After starting services, run the integration tests:
```bash
python test_integrations.py
```

The test script will verify:
1. Redis connections (both cache and Celery)
2. MailHog email sending
3. Celery task execution
4. API endpoints

Each test will show a clear ✓ (pass) or ✗ (fail) indicator, making it easy to spot any issues.

## Checking Results

1. View sent emails in MailHog:
   - Open http://localhost:8025 in your browser
   - Check received emails from CSV exports and notifications

2. Monitor Background Tasks:
   - Check terminal output for Celery worker logs
   - Verify scheduled tasks execution in logs
   - Watch for successful email deliveries

3. Test CSV Export:
   - Login as admin (admin@iitm.ac.in / pass)
   - Go to Summary Admin page
   - Click "Export User Data"
   - Check email in MailHog for the CSV file

## Stopping Services

To stop all services:
```bash
./stop_services.sh
```

The script will automatically stop:
- Flask application
- Celery workers
- Celery beat
- MailHog
- Redis server

## Troubleshooting

1. If Redis fails to start:
   - Check if port 6379 is free
   - Ensure Redis server is installed properly
   - Check error messages in terminal

2. If MailHog fails:
   - Verify ports 1025 and 8025 are available
   - Check MailHog installation
   - Look for error messages in terminal

3. If Celery tasks fail:
   - Check Redis connection
   - Verify worker is running
   - Check timezone settings

4. If tests fail:
   - Run test script with Python's verbose mode: `python -v test_integrations.py`
   - Check each service's status in test output
   - Review error messages for specific failures

## Task Schedule

1. Daily Reminders:
   - Time: 6:00 PM IST (Asia/Kolkata)
   - Checks: Inactive users and new quizzes
   - Sends: Email notifications

2. Monthly Reports:
   - Time: 00:00 IST on 1st of every month
   - Generates: Activity reports
   - Sends: Email with statistics

## Security

1. API Security:
   - All endpoints require authentication token
   - Export feature limited to admin role
   - CSRF protection enabled

2. Data Protection:
   - Email validation before sending
   - Secure token handling
   - Role-based access control

## Monitoring

1. Watch Logs:
   - Check terminal output for all services
   - Monitor Celery worker logs
   - Check Flask application logs

2. Service Status:
   - Use test script to verify all components
   - Check web interfaces (MailHog)
   - Monitor task execution

## Common Commands

Start everything:
```bash
./start_services.sh
```

Run tests:
```bash
python test_integrations.py
```

Stop everything:
```bash
./stop_services.sh
```

## Note on Redis

The implementation uses Redis with two databases:
- DB 0: For Flask caching
- DB 1: For Celery broker

This separation ensures that caching operations don't interfere with background tasks.