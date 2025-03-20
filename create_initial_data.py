from flask_security import SQLAlchemySessionUserDatastore
from extensions import db
from flask_security.utils import hash_password
from models import Subject, Chapter, Quiz, Questions, Scores
from datetime import datetime, timedelta, UTC
import logging
import random
from typing import List, Dict

# Configure logging
logger = logging.getLogger(__name__)

# Sample data configuration
SUBJECTS = [
    {"name": "Mathematics", "chapters": [
        "Calculus", "Algebra", "Geometry", "Statistics"
    ]},
    {"name": "Physics", "chapters": [
        "Mechanics", "Thermodynamics", "Electromagnetism", "Optics"
    ]},
    {"name": "Computer Science", "chapters": [
        "Programming", "Data Structures", "Algorithms", "Databases"
    ]}
]

SAMPLE_USERS = [
    {
        "email": "admin@iitm.ac.in",
        "password": "pass",
        "roles": ["admin"],
        "full_name": "Admin User",
        "qualification": "PhD in Computer Science",
        "dob": "1980-01-01"
    },
    {
        "email": "user@iitm.ac.in",
        "password": "pass",
        "roles": ["user"],
        "full_name": "Regular User",
        "qualification": "BSc Mathematics",
        "dob": "1995-01-01"
    },
    {
        "email": "student1@iitm.ac.in",
        "password": "pass",
        "roles": ["user"],
        "full_name": "Student One",
        "qualification": "BSc Physics",
        "dob": "1998-05-15"
    },
    {
        "email": "student2@iitm.ac.in",
        "password": "pass",
        "roles": ["user"],
        "full_name": "Student Two",
        "qualification": "BSc Computer Science",
        "dob": "1997-08-22"
    }
]

def create_question_bank() -> Dict[str, List[Dict]]:
    """Create a bank of sample questions for each subject"""
    return {
        "Mathematics": [
            {
                "question": "What is the derivative of x^2?",
                "option1": "2x",
                "option2": "x^2",
                "correct_answer": "2x"
            },
            {
                "question": "What is the integral of 2x?",
                "option1": "x^2",
                "option2": "2x^2",
                "correct_answer": "x^2"
            }
        ],
        "Physics": [
            {
                "question": "What is Newton's first law?",
                "option1": "Law of Inertia",
                "option2": "Law of Action-Reaction",
                "correct_answer": "Law of Inertia"
            },
            {
                "question": "What is the unit of force?",
                "option1": "Newton",
                "option2": "Joule",
                "correct_answer": "Newton"
            }
        ],
        "Computer Science": [
            {
                "question": "What is a stack?",
                "option1": "LIFO data structure",
                "option2": "FIFO data structure",
                "correct_answer": "LIFO data structure"
            },
            {
                "question": "What is SQL?",
                "option1": "Query Language",
                "option2": "Programming Language",
                "correct_answer": "Query Language"
            }
        ]
    }

def create_data(user_datastore: SQLAlchemySessionUserDatastore):
    """Create initial data with proper error handling and logging"""
    try:
        logger.info("Starting initial data creation")

        # Create roles
        logger.info("Creating roles")
        admin_role = user_datastore.find_or_create_role(
            name='admin', 
            description="Administrator"
        )
        user_role = user_datastore.find_or_create_role(
            name='user', 
            description="User"
        )

        # Create users
        logger.info("Creating users")
        users = []
        for user_data in SAMPLE_USERS:
            if not user_datastore.find_user(email=user_data["email"]):
                user = user_datastore.create_user(
                    email=user_data["email"],
                    password=hash_password(user_data["password"]),
                    roles=user_data["roles"],
                    full_name=user_data["full_name"],
                    qualification=user_data["qualification"],
                    dob=datetime.strptime(user_data["dob"], "%Y-%m-%d").date(),
                    active=True
                )
                users.append(user)
                logger.info(f"Created user: {user_data['email']}")

        # Create subjects and chapters
        logger.info("Creating subjects and chapters")
        question_bank = create_question_bank()
        subjects = {}
        
        for subject_data in SUBJECTS:
            subject = Subject(name=subject_data["name"])
            db.session.add(subject)
            subjects[subject.name] = subject
            
            for chapter_name in subject_data["chapters"]:
                chapter = Chapter(
                    name=chapter_name,
                    subject_id=subject.id,
                    description=f"Sample chapter for {chapter_name}"
                )
                db.session.add(chapter)
                
                # Create quizzes for each chapter
                for i in range(2):  # 2 quizzes per chapter
                    quiz = Quiz(
                        name=f"{chapter_name} Quiz {i+1}",
                        chapter_id=chapter.id,
                        date_of_quiz=datetime.now(UTC) + timedelta(days=i*7),
                        time_duration=30,
                        remarks=f"Sample quiz for {chapter_name}"
                    )
                    db.session.add(quiz)
                    
                    # Add questions to quiz
                    sample_questions = question_bank[subject.name]
                    for q_data in sample_questions:
                        question = Questions(
                            quiz_id=quiz.id,
                            question_statement=q_data["question"],
                            option1=q_data["option1"],
                            option2=q_data["option2"],
                            correct_answer=q_data["correct_answer"]
                        )
                        db.session.add(question)

        db.session.commit()

        # Create sample scores
        logger.info("Creating sample scores")
        for user in users:
            if 'user' in [role.name for role in user.roles]:
                quizzes = Quiz.query.all()
                for quiz in random.sample(quizzes, k=min(5, len(quizzes))):
                    score = Scores(
                        quiz_id=quiz.id,
                        user_id=user.id,
                        time_stamp_of_attempt=datetime.now(UTC) - timedelta(days=random.randint(1, 30)),
                        total_scored=random.randint(5, 10)
                    )
                    db.session.add(score)

        db.session.commit()
        logger.info("Successfully created initial data")

    except Exception as e:
        logger.error(f"Error creating initial data: {str(e)}")
        db.session.rollback()
        raise

def reset_data():
    """Reset all data in the database"""
    try:
        logger.info("Resetting database")
        # Delete in correct order to respect foreign keys
        Scores.query.delete()
        Questions.query.delete()
        Quiz.query.delete()
        Chapter.query.delete()
        Subject.query.delete()
        db.session.commit()
        logger.info("Database reset successful")
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        db.session.rollback()
        raise
