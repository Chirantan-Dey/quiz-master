from celery import Celery
from celery.schedules import crontab
from flask_excel import make_response_from_array, init_excel
from datetime import datetime, timedelta
from flask_mail import Message
import pytz
from functools import wraps
import traceback
import os
import sys
import io

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
    CELERY_BEAT_SCHEDULE = {
        'evening-reminder': {
            'task': 'workers.send_daily_reminders',
            'schedule': crontab(hour=18, minute=0)
        },
        'monthly-report': {
            'task': 'workers.send_monthly_reports',
            'schedule': crontab(0, 0, day_of_month='1')
        }
    }

# Update Celery config
celery.conf.update(
    broker_url=Config.CELERY_BROKER_URL,
    result_backend=Config.CELERY_RESULT_BACKEND,
    timezone=Config.CELERY_TIMEZONE,
    task_serializer=Config.CELERY_TASK_SERIALIZER,
    accept_content=Config.CELERY_ACCEPT_CONTENT,
    result_serializer=Config.CELERY_RESULT_SERIALIZER,
    task_ignore_result=Config.CELERY_TASK_IGNORE_RESULT,
    beat_schedule=Config.CELERY_BEAT_SCHEDULE
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

def generate_csv(data):
    """Generate CSV data from array"""
    try:
        response = make_response_from_array(data, "csv")
        if response and hasattr(response, 'get_data'):
            return response.get_data()
        else:
            # Fallback to manual CSV generation
            print("Falling back to manual CSV generation")  # Debug log
            output = io.StringIO()
            for row in data:
                output.write(','.join(str(cell) for cell in row) + '\n')
            return output.getvalue().encode('utf-8')
    except Exception as e:
        print(f"CSV generation error: {str(e)}")  # Debug log
        raise

@celery.task(ignore_result=False)
@ensure_context
@log_task_status("user_export")
def generate_user_export(admin_email):
    """Generate CSV export using flask-excel"""
    # Lazy imports to avoid circular dependency
    from models import User
    from extensions import mail
    from flask import current_app
    
    print(f"Starting export for {admin_email}")  # Debug log
    
    # Verify admin role
    user = User.query.filter_by(email=admin_email).first()
    if not user or 'admin' not in [role.name for role in user.roles]:
        error_msg = f"Unauthorized export attempt by {admin_email}"
        print(error_msg)  # Debug log
        raise ValueError('Unauthorized access')
        
    print("Generating user data...")  # Debug log
    
    data = [['User ID', 'Name', 'Email', 'Total Quizzes', 'Average Score', 'Last Quiz Date']]
    
    users = User.query.all()
    for user in users:
        scores = user.scores
        total_quizzes = len(scores)
        avg_score = sum(s.total_scored for s in scores)/total_quizzes if total_quizzes > 0 else 0
        last_quiz = max((s.time_stamp_of_attempt for s in scores), default=None) if scores else None
        
        data.append([
            user.id,
            user.full_name or 'N/A',
            user.email,
            total_quizzes,
            f"{avg_score:.2f}",
            last_quiz.strftime('%Y-%m-%d %H:%M:%S') if last_quiz else 'Never'
        ])
    
    print(f"Generated data for {len(users)} users")  # Debug log
    
    try:
        # Generate CSV
        print("Generating CSV file...")  # Debug log
        csv_data = generate_csv(data)
        
        # Send email
        message = Message(
            'Quiz Master - User Data Export',
            sender='quiz-master@example.com',
            recipients=[admin_email]
        )
        message.html = f"""
        <h2>User Data Export</h2>
        <p>Your requested export is attached.</p>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        message.attach(
            "user_export.csv",
            "text/csv",
            csv_data
        )
        
        print(f"Sending export email to {admin_email}")  # Debug log
        mail.send(message)
        
        print(f"Export completed and sent to {admin_email}")  # Debug log
        return "Export completed and sent"
    except Exception as e:
        error_msg = f"Export failed: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_msg)  # Debug log
        raise

# Only include celery.py in Python path when running as main module
if __name__ == '__main__':
    celery.start()