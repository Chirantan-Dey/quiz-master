from extensions import celery, db
from datetime import datetime, timedelta, UTC
from sqlalchemy import func
from flask import render_template, current_app
from models import User, Quiz, Scores
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging
import os
import jinja2
from typing import Dict, Any
from sqlalchemy import text

logger = logging.getLogger('celery')

def validate_template(template_name: str, context: Dict[str, Any]) -> bool:
    """
    Validate that a template exists and can be rendered with given context
    """
    try:
        template = current_app.jinja_env.get_template(template_name)
        template.render(context)
        return True
    except (jinja2.TemplateNotFound, jinja2.TemplateError) as e:
        logger.error(f"Template validation failed for {template_name}: {str(e)}")
        return False

def send_email(to_email: str, subject: str, html_content: str, attachments: Dict = None) -> bool:
    """
    Utility function to send emails using MailHog with better error handling and validation
    """
    if not isinstance(to_email, str) or '@' not in to_email:
        logger.error(f"Invalid email address: {to_email}")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = "noreply@quizmaster.com"
        msg['To'] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Attach files if any
        if attachments:
            for filename, content in attachments.items():
                try:
                    attachment = MIMEApplication(content)
                    attachment['Content-Disposition'] = f'attachment; filename="{filename}"'
                    msg.attach(attachment)
                except Exception as e:
                    logger.error(f"Failed to attach {filename}: {str(e)}")
                    continue

        # Connect to MailHog with proper error handling and timeout
        with smtplib.SMTP('localhost', 1025, timeout=10) as server:
            server.send_message(msg)
            logger.info(f"Email sent successfully to {to_email}")
            return True

    except Exception as e:
        logger.error(f"Email sending failed to {to_email}: {str(e)}")
        return False

def process_users_in_batches(query, batch_size=100):
    """
    Process users in batches to manage memory usage
    """
    offset = 0
    while True:
        batch = query.limit(batch_size).offset(offset).all()
        if not batch:
            break
        yield batch
        offset += batch_size

@celery.task(bind=True, max_retries=3, default_retry_delay=300, 
             retry_backoff=True, retry_jitter=True)
def send_daily_reminder(self):
    """
    Task to send daily reminders to users about new quizzes or if they haven't visited
    """
    from app import app

    try:
        with app.app_context():
            now = datetime.now(UTC)
            today = now.date()
            yesterday = today - timedelta(days=1)

            user_query = User.query.filter(User.active == True)
            
            # Process users in batches
            for user_batch in process_users_in_batches(user_query):
                for user in user_batch:
                    try:
                        last_attempt = Scores.query.filter_by(user_id=user.id)\
                            .order_by(Scores.time_stamp_of_attempt.desc())\
                            .first()

                        new_quizzes = Quiz.query.filter(
                            Quiz.date_of_quiz >= yesterday
                        ).all()

                        if (last_attempt and last_attempt.time_stamp_of_attempt.date() < yesterday) or new_quizzes:
                            context = {
                                'user': user,
                                'new_quizzes': new_quizzes,
                                'last_attempt': last_attempt
                            }

                            if validate_template('emails/daily_reminder.html', context):
                                html_content = render_template(
                                    'emails/daily_reminder.html',
                                    **context
                                )

                                if send_email(
                                    to_email=user.email,
                                    subject="Quiz Master - Daily Activity Reminder",
                                    html_content=html_content
                                ):
                                    logger.info(f"Daily reminder sent to {user.email}")
                                else:
                                    logger.warning(f"Failed to send daily reminder to {user.email}")

                    except Exception as user_error:
                        logger.error(f"Error processing user {user.email}: {str(user_error)}")
                        continue

            return True

    except Exception as e:
        logger.error(f"Daily reminder task failed: {str(e)}")
        self.retry(exc=e)

@celery.task(bind=True, max_retries=3, default_retry_delay=600,
             retry_backoff=True, retry_jitter=True)
def send_monthly_report(self):
    """
    Task to send monthly activity reports to users
    """
    from app import app

    try:
        with app.app_context():
            now = datetime.now(UTC)
            today = now.date()
            first_day = today.replace(day=1)
            last_month = first_day - timedelta(days=1)
            first_day_last_month = last_month.replace(day=1)

            user_query = User.query.filter(User.active == True)

            for user_batch in process_users_in_batches(user_query):
                for user in user_batch:
                    try:
                        # Use efficient querying
                        monthly_stats = db.session.execute(text("""
                            SELECT 
                                COUNT(*) as total_quizzes,
                                AVG(total_scored) as avg_score,
                                RANK() OVER (ORDER BY AVG(total_scored) DESC) as user_rank
                            FROM scores
                            WHERE user_id = :user_id
                            AND time_stamp_of_attempt >= :start_date
                            AND time_stamp_of_attempt < :end_date
                            GROUP BY user_id
                        """), {
                            'user_id': user.id,
                            'start_date': first_day_last_month,
                            'end_date': first_day
                        }).first()

                        if monthly_stats and monthly_stats.total_quizzes > 0:
                            monthly_scores = Scores.query.filter(
                                Scores.user_id == user.id,
                                Scores.time_stamp_of_attempt >= first_day_last_month,
                                Scores.time_stamp_of_attempt < first_day
                            ).all()

                            context = {
                                'user': user,
                                'total_quizzes': monthly_stats.total_quizzes,
                                'avg_score': monthly_stats.avg_score,
                                'rank': monthly_stats.user_rank,
                                'month': last_month.strftime('%B %Y'),
                                'scores': monthly_scores
                            }

                            if validate_template('emails/monthly_report.html', context):
                                html_content = render_template(
                                    'emails/monthly_report.html',
                                    **context
                                )

                                if send_email(
                                    to_email=user.email,
                                    subject=f"Quiz Master - Monthly Activity Report - {last_month.strftime('%B %Y')}",
                                    html_content=html_content
                                ):
                                    logger.info(f"Monthly report sent to {user.email}")
                                else:
                                    logger.warning(f"Failed to send monthly report to {user.email}")

                    except Exception as user_error:
                        logger.error(f"Error processing monthly report for user {user.email}: {str(user_error)}")
                        continue

            return True

    except Exception as e:
        logger.error(f"Monthly report task failed: {str(e)}")
        self.retry(exc=e)

@celery.task(bind=True, max_retries=3, default_retry_delay=300,
             retry_backoff=True, retry_jitter=True)
def generate_quiz_report(self, user_id: int) -> bool:
    """
    Task to generate and email a CSV report of user's quiz history
    """
    from app import app

    try:
        with app.app_context():
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Use chunked processing for large datasets
            CHUNK_SIZE = 1000
            chunks = []
            
            query = (
                db.session.query(
                    Quiz.id.label('quiz_id'),
                    Quiz.name.label('quiz_name'),
                    Quiz.chapter_id,
                    Quiz.date_of_quiz,
                    Scores.time_stamp_of_attempt,
                    Scores.total_scored,
                    Quiz.remarks
                )
                .join(Scores, Quiz.id == Scores.quiz_id)
                .filter(Scores.user_id == user_id)
                .order_by(Scores.time_stamp_of_attempt.desc())
            )

            # Process in chunks to manage memory
            for chunk_df in pd.read_sql(query.statement, db.session.bind, chunksize=CHUNK_SIZE):
                chunks.append(chunk_df)

            if not chunks:
                logger.warning(f"No quiz data found for user {user_id}")
                return False

            # Combine chunks and generate CSV
            df = pd.concat(chunks)
            csv_data = df.to_csv(index=False)

            context = {'user': user}
            if validate_template('emails/export_ready.html', context):
                html_content = render_template(
                    'emails/export_ready.html',
                    **context
                )

                if send_email(
                    to_email=user.email,
                    subject="Quiz Master - Your Quiz History Export",
                    html_content=html_content,
                    attachments={'quiz_history.csv': csv_data.encode()}
                ):
                    logger.info(f"Quiz report generated and sent to {user.email}")
                    return True
                else:
                    logger.warning(f"Failed to send quiz report to {user.email}")
                    return False

    except Exception as e:
        logger.error(f"Quiz report generation failed: {str(e)}")
        self.retry(exc=e)

    return False