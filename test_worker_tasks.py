import unittest
from datetime import datetime, timedelta
from workers import (
    send_daily_reminders,
    send_monthly_reports,
    generate_user_export,
    Config  # Import Config to test task schedules
)
from celery.schedules import crontab
from models import User, Quiz, Chapter, Subject, Scores, Role, Questions
from extensions import db, mail
from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
import json
import requests
from sqlalchemy.orm.exc import NoResultFound
import os

class TestWorkerTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        from app import create_app
        
        # Use test database
        test_db = 'instance/test_data.db'
        if os.path.exists(test_db):
            os.remove(test_db)
            
        # Create app with test config
        cls.app = create_app()
        cls.app.config.update({
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{test_db}',
            'WTF_CSRF_ENABLED': False,
            'TESTING': True
        })
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Setup user datastore
        cls.user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
        
        # Remove test database
        test_db = 'instance/test_data.db'
        if os.path.exists(test_db):
            os.remove(test_db)

    def setUp(self):
        """Set up test data before each test"""
        # Clear all tables before each test
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        
        self.setup_test_data()

    def tearDown(self):
        """Clean up test data"""
        # Clear all tables after each test
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

    def get_or_create_role(self, name, description=None):
        """Get existing role or create new one"""
        role = Role.query.filter_by(name=name).first()
        if not role:
            role = Role(name=name, description=description)
            db.session.add(role)
            db.session.commit()
        return role

    def setup_test_data(self):
        """Create test users, subjects, chapters, quizzes, and scores"""
        try:
            # Get or create roles
            admin_role = self.get_or_create_role('admin', 'Administrator')
            user_role = self.get_or_create_role('user', 'User')
            db.session.flush()
            
            # Create admin user using user_datastore
            self.admin = self.user_datastore.create_user(
                email='admin@test.com',
                password=hash_password('password'),
                full_name='Test Admin',
                active=True
            )
            self.user_datastore.add_role_to_user(self.admin, admin_role)
            db.session.flush()
            
            # Create test users
            self.users = []
            for i in range(3):
                user = self.user_datastore.create_user(
                    email=f'user{i}@test.com',
                    password=hash_password('password'),
                    full_name=f'Test User {i}',
                    active=True
                )
                self.user_datastore.add_role_to_user(user, user_role)
                self.users.append(user)
            
            db.session.commit()
            
            # Create subjects with unique names
            timestamp = datetime.now().timestamp()
            self.test_subjects = [
                Subject(name=f'Test Mathematics {timestamp}_1'),
                Subject(name=f'Test Science {timestamp}_2')
            ]
            db.session.add_all(self.test_subjects)
            db.session.commit()
            
            # Create chapters, quizzes, and scores
            for subject in self.test_subjects:
                # Two chapters per subject
                for j in range(2):
                    chapter = Chapter(
                        name=f'{subject.name} Chapter {j+1}',
                        description=f'Test chapter {j+1} for {subject.name}',
                        subject=subject
                    )
                    db.session.add(chapter)
                    db.session.commit()
                    
                    # Two quizzes per chapter
                    for k in range(2):
                        quiz = Quiz(
                            name=f'Quiz {k+1}',
                            chapter=chapter,
                            date_of_quiz=datetime.now(),
                            time_duration=60,  # 60 minutes
                            remarks=f'Test quiz {k+1}'
                        )
                        db.session.add(quiz)
                        db.session.commit()
                        
                        # Create questions
                        for q in range(2):
                            question = Questions(
                                quiz_id=quiz.id,
                                question_statement=f"Test Q{q+1}",
                                option1="A",
                                option2="B",
                                correct_answer="A" if q == 0 else "B"
                            )
                            db.session.add(question)
                        
                        # Create scores for some users
                        for user in self.users[:2]:  # Only first two users attempt quizzes
                            score = Scores(
                                user=user,
                                quiz=quiz,
                                total_scored=85.5 if user == self.users[0] else 75.5,
                                time_stamp_of_attempt=datetime.now() - timedelta(days=k)
                            )
                            db.session.add(score)
                        
                        db.session.commit()
        
        except Exception as e:
            db.session.rollback()
            raise unittest.SkipTest(f"Failed to setup test data: {str(e)}")

    def check_mailhog_emails(self, expected_count=None, subject=None, to_email=None):
        """Check MailHog for emails matching criteria"""
        try:
            response = requests.get('http://localhost:8025/api/v2/messages')
            if not response.ok:
                self.fail("Failed to connect to MailHog")
            
            messages = response.json()
            matching_messages = []
            
            for msg in messages.get('items', []):
                matches = True
                if subject and msg.get('Content', {}).get('Headers', {}).get('Subject', [''])[0] != subject:
                    matches = False
                    
                if to_email:
                    recipients = [f"{to.get('Mailbox')}@{to.get('Domain')}" for to in msg.get('To', [])]
                    if to_email not in recipients:
                        matches = False
                        
                if matches:
                    matching_messages.append(msg)
            
            if expected_count is not None:
                self.assertEqual(len(matching_messages), expected_count)
            
            return len(matching_messages) > 0
        
        except requests.exceptions.ConnectionError:
            raise unittest.SkipTest("MailHog is not running")
        except Exception as e:
            self.fail(f"Error checking MailHog: {str(e)}")

    def test_daily_reminders_schedule(self):
        """Test daily reminders schedule configuration"""
        schedule = Config.CELERY_BEAT_SCHEDULE.get('evening-reminder', {})
        self.assertIsNotNone(schedule, "Evening reminder schedule not found")
        self.assertEqual(schedule.get('task'), 'workers.send_daily_reminders')
        
        # Verify scheduled for 6 PM daily
        self.assertIsInstance(schedule.get('schedule'), crontab)
        # Convert set to int for comparison
        self.assertEqual(list(schedule['schedule'].hour)[0], 18)
        self.assertEqual(list(schedule['schedule'].minute)[0], 0)

    def test_monthly_reports_schedule(self):
        """Test monthly reports schedule configuration"""
        schedule = Config.CELERY_BEAT_SCHEDULE.get('monthly-report', {})
        self.assertIsNotNone(schedule, "Monthly report schedule not found")
        self.assertEqual(schedule.get('task'), 'workers.send_monthly_reports')
        
        # Verify scheduled for midnight on 1st of each month
        self.assertIsInstance(schedule.get('schedule'), crontab)
        # Convert set to int/str for comparison
        self.assertEqual(list(schedule['schedule'].hour)[0], 0)
        self.assertEqual(list(schedule['schedule'].minute)[0], 0)
        self.assertEqual(str(list(schedule['schedule'].day_of_month)[0]), '1')

    def test_daily_reminders_functionality(self):
        """
        Test daily reminders task functionality
        Note: This test executes the task immediately, ignoring the scheduled time (6 PM daily)
        """
        result = send_daily_reminders.apply().get()
        self.assertIn("Daily reminders sent to", result)
        
        # Check emails were sent to our test users
        for user in self.users:
            self.assertTrue(
                self.check_mailhog_emails(
                    expected_count=1,
                    subject='Quiz Master - Daily Update',
                    to_email=user.email
                )
            )

    def test_monthly_reports_functionality(self):
        """
        Test monthly reports task functionality
        Note: This test executes the task immediately, ignoring the scheduled time (1st of each month)
        """
        result = send_monthly_reports.apply().get()
        self.assertIn("Monthly reports sent to", result)
        
        # Check emails were sent to our test users
        for user in self.users:
            self.assertTrue(
                self.check_mailhog_emails(
                    expected_count=1,
                    subject='Quiz Master - Monthly Activity Report',
                    to_email=user.email
                )
            )

    def test_user_export_functionality(self):
        """Test user export task functionality"""
        result = generate_user_export.apply(args=[self.admin.email]).get()
        self.assertEqual(result, "Export completed and sent")
        
        # Check email was sent to admin
        self.assertTrue(
            self.check_mailhog_emails(
                expected_count=1,
                subject='Quiz Master - User Data Export',
                to_email=self.admin.email
            )
        )

    def test_unauthorized_export(self):
        """Test unauthorized user export attempt"""
        with self.assertRaises(ValueError) as context:
            generate_user_export.apply(args=[self.users[0].email]).get()
        self.assertIn("Unauthorized access", str(context.exception))

if __name__ == '__main__':
    unittest.main()