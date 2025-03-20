import unittest
from flask import Flask
from flask_testing import TestCase
from extensions import db, celery
from models import User, Quiz, Scores, Chapter, Subject
from workers import generate_quiz_report, send_daily_reminder, send_monthly_report
from datetime import datetime, timedelta, UTC
import logging
import os
import tempfile
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCeleryTasks(TestCase):
    def create_app(self):
        """Create Flask test app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['CELERY_BROKER_URL'] = 'memory://'
        app.config['CELERY_RESULT_BACKEND'] = 'cache+memory://'
        
        # Initialize extensions
        db.init_app(app)
        return app

    def setUp(self):
        """Set up test database and sample data"""
        db.create_all()
        self.setup_test_data()
        
        # Create temporary directory for test logs
        self.test_log_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_log_dir, 'logs'), exist_ok=True)

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        
        # Clean up test logs
        import shutil
        shutil.rmtree(self.test_log_dir)

    def setup_test_data(self):
        """Create test data in database"""
        # Create test user
        user = User(
            email='test@example.com',
            password='test123',
            active=True,
            full_name='Test User',
            qualification='Test Qualification',
            dob=datetime.now(UTC).date()
        )
        db.session.add(user)

        # Create test subject and chapter
        subject = Subject(name='Test Subject')
        db.session.add(subject)
        db.session.flush()

        chapter = Chapter(
            name='Test Chapter',
            subject_id=subject.id,
            description='Test Description'
        )
        db.session.add(chapter)
        db.session.flush()

        # Create test quiz
        quiz = Quiz(
            name='Test Quiz',
            chapter_id=chapter.id,
            date_of_quiz=datetime.now(UTC).date(),
            time_duration=30,
            remarks='Test Quiz Remarks'
        )
        db.session.add(quiz)
        db.session.flush()

        # Create test scores
        score = Scores(
            quiz_id=quiz.id,
            user_id=user.id,
            time_stamp_of_attempt=datetime.now(UTC),
            total_scored=8
        )
        db.session.add(score)
        db.session.commit()

        self.test_user = user
        self.test_quiz = quiz
        self.test_score = score

    @patch('workers.send_email')
    def test_generate_quiz_report(self, mock_send_email):
        """Test quiz report generation task"""
        mock_send_email.return_value = True
        
        result = generate_quiz_report(self.test_user.id)
        self.assertTrue(result)
        mock_send_email.assert_called_once()
        
        # Verify email content
        call_args = mock_send_email.call_args[1]
        self.assertEqual(call_args['to_email'], self.test_user.email)
        self.assertIn('quiz_history.csv', call_args['attachments'])

    @patch('workers.send_email')
    def test_daily_reminder(self, mock_send_email):
        """Test daily reminder task"""
        mock_send_email.return_value = True
        
        # Test user with recent activity
        result = send_daily_reminder()
        self.assertTrue(result)
        
        # Test user without recent activity
        self.test_score.time_stamp_of_attempt = datetime.now(UTC) - timedelta(days=2)
        db.session.commit()
        
        result = send_daily_reminder()
        self.assertTrue(result)
        mock_send_email.assert_called()

    @patch('workers.send_email')
    def test_monthly_report(self, mock_send_email):
        """Test monthly report task"""
        mock_send_email.return_value = True
        
        # Create some scores from last month
        last_month = datetime.now(UTC) - timedelta(days=30)
        score = Scores(
            quiz_id=self.test_quiz.id,
            user_id=self.test_user.id,
            time_stamp_of_attempt=last_month,
            total_scored=9
        )
        db.session.add(score)
        db.session.commit()
        
        result = send_monthly_report()
        self.assertTrue(result)
        mock_send_email.assert_called()
        
        # Verify email content
        call_args = mock_send_email.call_args[1]
        self.assertEqual(call_args['to_email'], self.test_user.email)
        self.assertIn('Monthly Activity Report', call_args['subject'])

    @patch('workers.send_email')
    def test_email_failure_handling(self, mock_send_email):
        """Test handling of email sending failures"""
        mock_send_email.return_value = False
        
        # Test with failed email
        result = generate_quiz_report(self.test_user.id)
        self.assertFalse(result)

    def test_invalid_user(self):
        """Test task behavior with invalid user ID"""
        result = generate_quiz_report(999999)  # Non-existent user ID
        self.assertFalse(result)

    @patch('workers.send_email')
    def test_empty_quiz_history(self, mock_send_email):
        """Test report generation for user with no quiz history"""
        # Create new user with no scores
        new_user = User(
            email='empty@example.com',
            password='test123',
            active=True,
            full_name='Empty User'
        )
        db.session.add(new_user)
        db.session.commit()
        
        result = generate_quiz_report(new_user.id)
        self.assertFalse(result)  # Should return False for no data
        mock_send_email.assert_not_called()

    def test_task_retry_mechanism(self):
        """Test task retry mechanism"""
        with patch('workers.send_email') as mock_send_email:
            mock_send_email.side_effect = Exception('Simulated failure')
            
            with self.assertRaises(Exception):
                generate_quiz_report(self.test_user.id)

if __name__ == '__main__':
    unittest.main()