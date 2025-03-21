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
    """Test daily reminders with full quiz information"""
    try:
        logger.info("Starting daily reminders test")
        from models import User, Quiz, Scores, Role
        from extensions import mail
        logger.info("Imports successful")
        
        # Find inactive users (excluding admins)
        inactive_users = User.query.join(User.roles).filter(
            Role.name == 'user'
        ).limit(3).all()
        
        logger.info(f"Found {len(inactive_users)} users")
        
        # Get recent quizzes
        new_quizzes = Quiz.query.all()
        logger.info(f"Found {len(new_quizzes)} quizzes")
        
        sent_count = 0
        for user in inactive_users:
            # Get user's scores
            scores = user.scores
            attempted_quizzes = {s.quiz_id for s in scores}
            unattempted_quizzes = [q for q in new_quizzes if q.id not in attempted_quizzes]
            
            message = Message(
                'Quiz Master - Daily Update',
                sender='quiz-master@example.com',
                recipients=[user.email]
            )
            
            html_content = [
                f"<h2>Quiz Update for {user.full_name or user.email}</h2>",
                "<h3>Your Quiz Status:</h3>",
                f"<p>Total Quizzes Attempted: {len(scores)}</p>"
            ]
            
            if unattempted_quizzes:
                html_content.extend([
                    "<h3>New Quizzes Available:</h3>",
                    "<ul>"
                ])
                for quiz in unattempted_quizzes:
                    html_content.append(
                        f"<li><strong>{quiz.name}</strong> - {quiz.chapter.name}"
                        f"<br>Questions: {len(quiz.questions)}"
                        f"<br>Duration: {quiz.time_limit} minutes</li>"
                    )
                html_content.append("</ul>")
            
            message.html = "\n".join(html_content)
            
            try:
                logger.info(f"Sending reminder to {user.email}")
                mail.send(message)
                sent_count += 1
                logger.info(f"Reminder sent to {user.email}")
            except Exception as mail_error:
                logger.error(f"Failed to send reminder to {user.email}: {str(mail_error)}")
                logger.error(traceback.format_exc())
                raise
        
        result = f"Reminders sent to {sent_count} users"
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
    """Test monthly reports with detailed statistics"""
    try:
        logger.info("Starting monthly reports test")
        from models import User, Scores, Quiz, Subject
        from extensions import mail
        logger.info("Imports successful")
        
        users = User.query.limit(3).all()
        logger.info(f"Processing reports for {len(users)} users")
        sent_count = 0
        
        for user in users:
            # Get all user's scores
            scores = user.scores
            
            # Get subject-wise performance
            subject_scores = {}
            for score in scores:
                subject = score.quiz.chapter.subject
                if subject.name not in subject_scores:
                    subject_scores[subject.name] = {
                        'total_score': 0,
                        'count': 0,
                        'best_score': 0
                    }
                
                stats = subject_scores[subject.name]
                stats['total_score'] += score.total_scored
                stats['count'] += 1
                stats['best_score'] = max(stats['best_score'], score.total_scored)
            
            # Build HTML report
            html_content = [
                f"<h1>Monthly Activity Report for {user.full_name or user.email}</h1>",
                "<h2>Overall Statistics</h2>",
                "<ul>",
                f"<li>Total Quizzes Attempted: {len(scores)}</li>",
                f"<li>Overall Average Score: {sum(s.total_scored for s in scores)/len(scores):.2f}% (if scores)</li>",
                "</ul>",
                "<h2>Subject-wise Performance</h2>"
            ]
            
            for subject, stats in subject_scores.items():
                avg_score = stats['total_score'] / stats['count']
                html_content.extend([
                    f"<h3>{subject}</h3>",
                    "<ul>",
                    f"<li>Quizzes Attempted: {stats['count']}</li>",
                    f"<li>Average Score: {avg_score:.2f}%</li>",
                    f"<li>Best Score: {stats['best_score']:.2f}%</li>",
                    "</ul>"
                ])
            
            # Recent activity
            html_content.extend([
                "<h2>Recent Quiz Activity</h2>",
                "<table border='1'>",
                "<tr><th>Quiz</th><th>Score</th><th>Date</th></tr>"
            ])
            
            for score in sorted(scores, key=lambda s: s.time_stamp_of_attempt, reverse=True)[:5]:
                html_content.append(
                    f"<tr><td>{score.quiz.name}</td>"
                    f"<td>{score.total_scored:.2f}%</td>"
                    f"<td>{score.time_stamp_of_attempt.strftime('%Y-%m-%d %H:%M')}</td></tr>"
                )
            
            html_content.append("</table>")
            
            message = Message(
                'Quiz Master - Monthly Activity Report',
                sender='quiz-master@example.com',
                recipients=[user.email]
            )
            message.html = "\n".join(html_content)
            
            try:
                logger.info(f"Sending report to {user.email}")
                mail.send(message)
                sent_count += 1
                logger.info(f"Report sent to {user.email}")
            except Exception as mail_error:
                logger.error(f"Failed to send report to {user.email}: {str(mail_error)}")
                logger.error(traceback.format_exc())
                raise
        
        result = f"Monthly reports sent to {sent_count} users"
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
    """Test user export with comprehensive data"""
    try:
        logger.info("Starting export test")
        from models import User, Subject
        from extensions import mail
        logger.info("Imports successful")
        
        # Verify admin role
        user = User.query.filter_by(email=admin_email).first()
        if not user or 'admin' not in [role.name for role in user.roles]:
            error_msg = f"Unauthorized export attempt by {admin_email}"
            logger.error(error_msg)
            raise ValueError('Unauthorized access')
        
        users = User.query.all()
        logger.info(f"Exporting data for {len(users)} users")
        
        # Get all subjects for per-subject stats
        subjects = Subject.query.all()
        subject_names = [s.name for s in subjects]
        
        # Prepare headers
        headers = [
            'User ID', 'Name', 'Email', 
            'Total Quizzes', 'Overall Average', 'Best Score',
            'Last Quiz Date'
        ]
        # Add per-subject columns
        for subject in subject_names:
            headers.extend([
                f"{subject} Quizzes",
                f"{subject} Average",
                f"{subject} Best"
            ])
        
        data = [headers]
        
        for user in users:
            scores = user.scores
            user_row = [
                user.id,
                user.full_name or 'N/A',
                user.email,
                len(scores),
                f"{sum(s.total_scored for s in scores)/len(scores):.2f}%" if scores else "0%",
                f"{max(s.total_scored for s in scores):.2f}%" if scores else "0%",
                scores[-1].time_stamp_of_attempt.strftime('%Y-%m-%d %H:%M') if scores else 'Never'
            ]
            
            # Add subject-wise stats
            for subject in subject_names:
                subject_scores = [
                    s for s in scores 
                    if s.quiz.chapter.subject.name == subject
                ]
                user_row.extend([
                    len(subject_scores),
                    f"{sum(s.total_scored for s in subject_scores)/len(subject_scores):.2f}%" if subject_scores else "0%",
                    f"{max(s.total_scored for s in subject_scores):.2f}%" if subject_scores else "0%"
                ])
            
            data.append(user_row)
        
        # Generate CSV
        logger.info("Generating CSV file...")
        excel_file = make_response_from_array(data, "csv")
        
        # Send email
        message = Message(
            'Quiz Master - User Data Export',
            sender='quiz-master@example.com',
            recipients=[admin_email]
        )
        
        message.html = f"""
        <h2>User Data Export</h2>
        <p>Your requested export is attached. It contains:</p>
        <ul>
            <li>Overall user statistics</li>
            <li>Subject-wise performance breakdown</li>
            <li>Total of {len(users)} users</li>
            <li>Data for {len(subject_names)} subjects</li>
        </ul>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        message.attach(
            "user_export.csv",
            "text/csv",
            excel_file.get_data()
        )
        
        logger.info(f"Sending export to {admin_email}")
        mail.send(message)
        
        result = "Export completed and sent"
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
        test_celery.worker_main(['worker', '--loglevel=DEBUG', '--pool=solo'])
    else:
        sys.exit(test_tasks())