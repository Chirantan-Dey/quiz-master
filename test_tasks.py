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
import requests

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

def format_email_style():
    """Return CSS styles for email"""
    return """
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3, h4 {
            color: #2c3e50;
            margin-top: 20px;
        }
        h1 { font-size: 24px; color: #1a73e8; }
        h2 { font-size: 20px; color: #34495e; }
        h3 { font-size: 18px; color: #2980b9; }
        ul { 
            list-style-type: none;
            padding-left: 20px;
        }
        li {
            margin: 10px 0;
            padding: 5px;
            border-left: 3px solid #1a73e8;
            padding-left: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            color: #2c3e50;
        }
        .stats {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .highlight {
            color: #1a73e8;
            font-weight: bold;
        }
    </style>
    """

def format_email_html(content, title):
    """Format HTML content with styling"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        {format_email_style()}
    </head>
    <body>
        <h1>{title}</h1>
        {content}
    </body>
    </html>
    """

@test_celery.task(name='test.daily_reminders')
@ensure_context
@log_task_status("test_daily_reminders")
def test_daily_reminders():
    """Test daily reminders task"""
    try:
        logger.info("Starting daily reminders test")
        from models import User, Quiz, Role
        from extensions import mail
        logger.info("Imports successful")
        
        # Find users (excluding admins)
        users = User.query.join(User.roles).filter(Role.name == 'user').limit(3).all()
        logger.info(f"Found {len(users)} users")
        
        sent_count = 0
        for user in users:
            scores = user.scores
            attempted_quiz_ids = {s.quiz_id for s in scores}
            
            # Get unattempted quizzes
            quizzes = Quiz.query.all()
            unattempted = [q for q in quizzes if q.id not in attempted_quiz_ids]
            
            html_content = [
                f"<div class='stats'>",
                f"<h2>Hello {user.full_name or user.email}!</h2>",
                "<h3>Quiz Status</h3>",
                "<ul>",
                f"<li>Quizzes Attempted: <span class='highlight'>{len(scores)}</span></li>",
                f"<li>Quizzes Available: <span class='highlight'>{len(unattempted)}</span></li>"
            ]
            
            if scores:
                avg_score = sum(s.total_scored for s in scores)/len(scores)
                html_content.append(f"<li>Average Score: <span class='highlight'>{avg_score:.2f}%</span></li>")
            
            html_content.append("</ul></div>")
            
            if unattempted:
                html_content.extend([
                    "<h3>Available Quizzes</h3>",
                    "<table>",
                    "<tr><th>Quiz</th><th>Chapter</th><th>Subject</th><th>Questions</th></tr>"
                ])
                
                for quiz in unattempted:
                    html_content.append(
                        f"<tr>"
                        f"<td>{quiz.name}</td>"
                        f"<td>{quiz.chapter.name}</td>"
                        f"<td>{quiz.chapter.subject.name}</td>"
                        f"<td>{len(quiz.questions)}</td>"
                        f"</tr>"
                    )
                
                html_content.append("</table>")
                html_content.append("<p>Don't miss out on these learning opportunities!</p>")
            else:
                html_content.append("<p>Great job! You've attempted all available quizzes.</p>")
            
            message = Message(
                'Quiz Master - Daily Update',
                sender='quiz-master@example.com',
                recipients=[user.email]
            )
            message.html = format_email_html("\n".join(html_content), "Daily Quiz Update")
            
            try:
                logger.info(f"Sending reminder to {user.email}")
                mail.send(message)
                sent_count += 1
                logger.info(f"Reminder sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send reminder to {user.email}: {str(e)}")
                logger.error(traceback.format_exc())
                raise
        
        result = f"Daily reminders sent to {sent_count} users"
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
        from models import User, Quiz, Subject
        from extensions import mail
        logger.info("Imports successful")
        
        users = User.query.limit(3).all()
        logger.info(f"Processing reports for {len(users)} users")
        sent_count = 0
        
        for user in users:
            scores = user.scores
            
            # Get subject-wise performance
            subject_stats = {}
            for score in scores:
                subject = score.quiz.chapter.subject
                if subject.name not in subject_stats:
                    subject_stats[subject.name] = {
                        'total_score': 0,
                        'count': 0,
                        'best_score': 0,
                        'scores': []
                    }
                
                stats = subject_stats[subject.name]
                stats['total_score'] += score.total_scored
                stats['count'] += 1
                stats['best_score'] = max(stats['best_score'], score.total_scored)
                stats['scores'].append(score)
            
            # Build HTML content
            html_content = [
                "<div class='stats'>",
                "<h2>Overall Performance</h2>",
                "<ul>"
            ]
            
            if scores:
                avg_score = sum(s.total_scored for s in scores)/len(scores)
                html_content.extend([
                    f"<li>Total Quizzes: <span class='highlight'>{len(scores)}</span></li>",
                    f"<li>Average Score: <span class='highlight'>{avg_score:.2f}%</span></li>",
                    f"<li>Best Score: <span class='highlight'>{max(s.total_scored for s in scores):.2f}%</span></li>"
                ])
            else:
                html_content.append("<li>No quizzes attempted yet</li>")
            
            html_content.append("</ul></div>")
            
            if subject_stats:
                for subject, stats in subject_stats.items():
                    avg = stats['total_score'] / stats['count']
                    html_content.extend([
                        "<div class='stats'>",
                        f"<h3>{subject}</h3>",
                        "<ul>",
                        f"<li>Quizzes: <span class='highlight'>{stats['count']}</span></li>",
                        f"<li>Average: <span class='highlight'>{avg:.2f}%</span></li>",
                        f"<li>Best: <span class='highlight'>{stats['best_score']:.2f}%</span></li>",
                        "</ul>",
                        "<h4>Recent Attempts</h4>",
                        "<table>",
                        "<tr><th>Quiz</th><th>Score</th><th>Date</th><th>Questions</th></tr>"
                    ])
                    
                    recent = sorted(stats['scores'], key=lambda s: s.time_stamp_of_attempt, reverse=True)[:5]
                    for score in recent:
                        html_content.append(
                            f"<tr>"
                            f"<td>{score.quiz.name}</td>"
                            f"<td>{score.total_scored:.2f}%</td>"
                            f"<td>{score.time_stamp_of_attempt.strftime('%Y-%m-%d')}</td>"
                            f"<td>{len(score.quiz.questions)}</td>"
                            f"</tr>"
                        )
                    
                    html_content.extend([
                        "</table>",
                        "</div>"
                    ])
            
            message = Message(
                'Quiz Master - Monthly Activity Report',
                sender='quiz-master@example.com',
                recipients=[user.email]
            )
            message.html = format_email_html(
                "\n".join(html_content),
                f"Monthly Activity Report for {user.full_name or user.email}"
            )
            
            try:
                logger.info(f"Sending report to {user.email}")
                mail.send(message)
                sent_count += 1
                logger.info(f"Report sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send report to {user.email}: {str(e)}")
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
    """Test user export task"""
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
            'User ID', 'Name', 'Email', 'Roles',
            'Total Quizzes', 'Overall Average', 'Best Score',
            'Recent Quizzes (7 days)', 'Recent Average',
            'Last Quiz Date'
        ]
        # Add per-subject columns
        for subject in subject_names:
            headers.extend([
                f"{subject} Quizzes",
                f"{subject} Average",
                f"{subject} Best",
                f"{subject} Recent"
            ])
        
        data = [headers]
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        for user in users:
            scores = user.scores
            recent_scores = [s for s in scores if s.time_stamp_of_attempt >= week_ago]
            
            row = [
                user.id,
                user.full_name or 'N/A',
                user.email,
                ', '.join(role.name for role in user.roles)
            ]
            
            # Overall stats
            if scores:
                row.extend([
                    len(scores),
                    f"{sum(s.total_scored for s in scores)/len(scores):.2f}%",
                    f"{max(s.total_scored for s in scores):.2f}%",
                    len(recent_scores),
                    f"{sum(s.total_scored for s in recent_scores)/len(recent_scores):.2f}%" if recent_scores else "N/A",
                    scores[-1].time_stamp_of_attempt.strftime('%Y-%m-%d %H:%M')
                ])
            else:
                row.extend(['0', '0%', '0%', '0', 'N/A', 'Never'])
            
            # Subject-wise stats
            for subject in subject_names:
                subject_scores = [s for s in scores if s.quiz.chapter.subject.name == subject]
                recent_subject = [s for s in subject_scores if s.time_stamp_of_attempt >= week_ago]
                
                if subject_scores:
                    row.extend([
                        len(subject_scores),
                        f"{sum(s.total_scored for s in subject_scores)/len(subject_scores):.2f}%",
                        f"{max(s.total_scored for s in subject_scores):.2f}%",
                        f"{len(recent_subject)} in last 7 days"
                    ])
                else:
                    row.extend(['0', '0%', '0%', 'No activity'])
            
            data.append(row)
        
        # Generate CSV
        logger.info("Generating CSV file...")
        excel_file = make_response_from_array(data, "csv")
        
        # Send email
        message = Message(
            'Quiz Master - User Data Export',
            sender='quiz-master@example.com',
            recipients=[admin_email]
        )
        
        html_content = [
            "<div class='stats'>",
            "<h2>Export Summary</h2>",
            "<ul>",
            f"<li>Total Users: <span class='highlight'>{len(users)}</span></li>",
            f"<li>Subjects: <span class='highlight'>{len(subject_names)}</span></li>",
            f"<li>Data Points: <span class='highlight'>{len(headers)}</span></li>",
            "</ul>",
            "</div>",
            "<h3>Included Data</h3>",
            "<ul>",
            "<li>User details and roles</li>",
            "<li>Overall performance metrics</li>",
            "<li>Subject-wise breakdown</li>",
            "<li>Recent activity data</li>",
            "</ul>",
            "<p>Please find the detailed CSV export attached.</p>"
        ]
        
        message.html = format_email_html("\n".join(html_content), "User Data Export")
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