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

def format_email_style():
    """Return CSS styles for email templates"""
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
        h1, h2, h3, h4 { color: #2c3e50; margin-top: 20px; }
        h1 { font-size: 24px; color: #1a73e8; }
        h2 { font-size: 20px; color: #34495e; }
        h3 { font-size: 18px; color: #2980b9; }
        ul { list-style-type: none; padding-left: 20px; }
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
        th { background-color: #f8f9fa; color: #2c3e50; }
        .stats {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .highlight { color: #1a73e8; font-weight: bold; }
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
@log_task_status("daily_reminders")
def send_daily_reminders():
    """Send daily quiz reminders to users"""
    from models import User, Quiz, Role
    from extensions import mail
    
    # Find users (excluding admins)
    users = User.query.join(User.roles).filter(
        Role.name == 'user'
    ).all()
    
    sent_count = 0
    for user in users:
        try:
            scores = user.scores
            attempted_quiz_ids = {s.quiz_id for s in scores}
            
            # Get unattempted quizzes
            quizzes = Quiz.query.all()
            unattempted = [q for q in quizzes if q.id not in attempted_quiz_ids]
            
            html_content = [
                "<div class='stats'>",
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
            
            mail.send(message)
            sent_count += 1
            print(f"Reminder sent to {user.email}")  # Debug log
        except Exception as e:
            print(f"Failed to send reminder to {user.email}: {str(e)}")
            print(traceback.format_exc())
    
    return f"Daily reminders sent to {sent_count} users"

@celery.task(ignore_result=False)
@ensure_context
@log_task_status("monthly_reports")
def send_monthly_reports():
    """Send monthly performance reports to users"""
    from models import User, Quiz, Subject, Role
    from extensions import mail
    
    users = User.query.join(User.roles).filter(
        Role.name == 'user'
    ).all()
    
    sent_count = 0
    for user in users:
        try:
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
            
            mail.send(message)
            sent_count += 1
            print(f"Report sent to {user.email}")  # Debug log
        except Exception as e:
            print(f"Failed to send report to {user.email}: {str(e)}")
            print(traceback.format_exc())
            continue
    
    return f"Monthly reports sent to {sent_count} users"

@celery.task(ignore_result=False)
@ensure_context
@log_task_status("user_export")
def generate_user_export(admin_email):
    """Generate detailed user export"""
    from models import User, Subject, Role
    from extensions import mail
    
    # Verify admin role
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user or 'admin' not in [role.name for role in admin_user.roles]:
        raise ValueError('Unauthorized access')
    
    # Get non-admin users
    users = User.query.join(User.roles).filter(
        Role.name == 'user'
    ).all()
    
    # Get subjects for per-subject stats
    subjects = Subject.query.all()
    subject_names = [s.name for s in subjects]
    
    # Prepare headers
    headers = [
        'User ID', 'Name', 'Email',
        'Total Quizzes', 'Overall Average', 'Best Score',
        'Recent Quizzes (7 days)', 'Recent Average',
        'Last Quiz Date'
    ]
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
    
    try:
        csv_data = generate_csv(data)
        
        message = Message(
            'Quiz Master - User Data Export',
            sender='quiz-master@example.com',
            recipients=[admin_email]
        )
        message.html = format_email_html(
            f"""
            <h2>User Data Export</h2>
            <p>Your requested export is attached.</p>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """,
            "User Data Export"
        )
        message.attach(
            "user_export.csv",
            "text/csv",
            csv_data
        )
        
        mail.send(message)
        return "Export completed and sent"
        
    except Exception as e:
        error_msg = f"Export failed: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_msg)
        raise

# Only include celery.py in Python path when running as main module
if __name__ == '__main__':
    celery.start()