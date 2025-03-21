from celery import Celery
from celery.schedules import crontab
from flask_excel import make_response_from_array
from datetime import datetime, timedelta
from models import User, Quiz, Scores, Role, db
import charts  # Import the entire module
from extensions import mail, cache
from flask_mail import Message
from flask import current_app
import pytz
from functools import wraps
import traceback
from app import create_app

# Create Flask app for context
flask_app = create_app()

# Initialize Celery
celery = Celery('quiz_master')
celery.conf.update(
    broker_url='redis://localhost:6379/1',
    result_backend='redis://localhost:6379/1',  # Added result backend
    timezone='Asia/Kolkata',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_ignore_result=False,  # Enable result tracking
    beat_schedule={
        'evening-reminder': {
            'task': 'workers.send_daily_reminders',
            'schedule': crontab(hour=18, minute=0)  # 6 PM IST
        },
        'monthly-report': {
            'task': 'workers.send_monthly_reports',
            'schedule': crontab(0, 0, day_of_month='1')  # 1st of each month
        }
    }
)

def ensure_context(f):
    """Ensure function runs within Flask app context"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        with flask_app.app_context():
            print(f"Executing task with app context: {f.__name__}")  # Debug log
            return f(*args, **kwargs)
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

@celery.task(ignore_result=False)
@ensure_context
@log_task_status("daily_reminders")
def send_daily_reminders():
    """Send daily reminders to inactive users and notify about new quizzes"""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    yesterday = now - timedelta(days=1)
    
    print("Finding inactive users...")  # Debug log
    
    # Find inactive users (excluding admins)
    inactive_users = User.query.join(User.roles).filter(
        ~User.scores.any(Scores.time_stamp_of_attempt > yesterday),
        Role.name == 'user'  # Only send to regular users
    ).all()
    
    # Find new quizzes from last 24 hours
    new_quizzes = Quiz.query.filter(
        Quiz.date_of_quiz > yesterday,
        Quiz.date_of_quiz <= now  # Only include published quizzes
    ).all()
    
    if not inactive_users and not new_quizzes:
        print("No reminders needed")  # Debug log
        return "No reminders needed"
        
    for user in inactive_users:
        message = Message(
            'Quiz Master - Daily Update',
            sender='quiz-master@example.com',  # Added sender
            recipients=[user.email]
        )
        
        if new_quizzes:
            message.html = f"""
            <h2>New Quizzes Available!</h2>
            <p>Hello {user.full_name or user.email},</p>
            <p>The following new quizzes have been added:</p>
            <ul>
                {''.join(f'<li>{quiz.name} in {quiz.chapter.name}</li>' for quiz in new_quizzes)}
            </ul>
            """
        else:
            message.html = f"""
            <h2>Daily Reminder</h2>
            <p>Hello {user.full_name or user.email},</p>
            <p>Don't forget to practice your quizzes today!</p>
            """
        
        try:
            mail.send(message)
            print(f"Reminder sent to {user.email}")  # Debug log
        except Exception as e:
            print(f"Failed to send reminder to {user.email}: {str(e)}")  # Debug log
            raise
    
    return f"Sent reminders to {len(inactive_users)} users"

@celery.task(ignore_result=False)
@ensure_context
@log_task_status("monthly_reports")
def send_monthly_reports():
    """Generate and send monthly activity reports"""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    last_month = now.replace(day=1) - timedelta(days=1)
    month_start = last_month.replace(day=1)
    
    print("Generating monthly reports...")  # Debug log
    
    # Get all users
    users = User.query.all()
    sent_count = 0
    
    for user in users:
        # Get user's scores for last month
        monthly_scores = Scores.query.filter(
            Scores.user_id == user.id,
            Scores.time_stamp_of_attempt >= month_start,
            Scores.time_stamp_of_attempt <= last_month
        ).all()
        
        if not monthly_scores:
            print(f"No activity for user {user.email}, skipping report")  # Debug log
            continue
        
        # Generate user's charts
        print(f"Generating charts for user {user.email}")  # Debug log
        charts.cleanup_charts()
        attempts_chart = charts.generate_user_subject_attempts()(user.id)
        
        message = Message(
            f'Monthly Activity Report - {last_month.strftime("%B %Y")}',
            sender='quiz-master@example.com',  # Added sender
            recipients=[user.email]
        )
        
        total_quizzes = len(monthly_scores)
        avg_score = sum(s.total_scored for s in monthly_scores) / total_quizzes
        
        message.html = f"""
        <h1>Monthly Activity Report - {last_month.strftime("%B %Y")}</h1>
        <p>Hello {user.full_name or user.email},</p>
        
        <h2>Your Activity Summary</h2>
        <ul>
            <li>Quizzes Completed: {total_quizzes}</li>
            <li>Average Score: {avg_score:.2f}</li>
        </ul>
        """
        
        try:
            mail.send(message)
            print(f"Monthly report sent to {user.email}")  # Debug log
            sent_count += 1
        except Exception as e:
            print(f"Failed to send monthly report to {user.email}: {str(e)}")  # Debug log
            raise
    
    return f"Sent monthly reports to {sent_count} active users"

@celery.task(ignore_result=False)
@ensure_context
@log_task_status("user_export")
def generate_user_export(admin_email):
    """Generate CSV export using flask-excel"""
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
        excel_file = make_response_from_array(data, "csv")
        
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
            excel_file.get_data()
        )
        
        print(f"Sending export email to {admin_email}")  # Debug log
        mail.send(message)
        
        print(f"Export completed and sent to {admin_email}")  # Debug log
        return "Export completed and sent"
    except Exception as e:
        error_msg = f"Export failed: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_msg)  # Debug log
        raise