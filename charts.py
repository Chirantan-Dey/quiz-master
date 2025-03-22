import os
import matplotlib
matplotlib.use('Agg')  # Required for server-side rendering
import matplotlib.pyplot as plt
from models import Subject, Chapter, Quiz, Questions, Scores, db
from sqlalchemy import func
from datetime import datetime

CHARTS_DIR = os.path.join('static', 'charts')
ADMIN_CHARTS_DIR = os.path.join(CHARTS_DIR, 'admin')
USER_CHARTS_DIR = os.path.join(CHARTS_DIR, 'user')

# Create directories if they don't exist
for directory in [CHARTS_DIR, ADMIN_CHARTS_DIR, USER_CHARTS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def cleanup_charts():
    """Delete all existing chart files"""
    for directory in [ADMIN_CHARTS_DIR, USER_CHARTS_DIR]:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error deleting {filepath}: {str(e)}")

def generate_admin_subject_scores():
    """Generate bar chart for subject-wise top scores"""
    # Get subject-wise top scores
    result = db.session.query(
        Subject.name,
        func.max(Scores.total_scored).label('top_score')
    ).join(
        Chapter, Subject.id == Chapter.subject_id
    ).join(
        Quiz, Chapter.id == Quiz.chapter_id
    ).join(
        Scores, Quiz.id == Scores.quiz_id
    ).group_by(
        Subject.name
    ).all()
    
    if not result:
        return None
    
    subjects = [r[0] for r in result]
    scores = [r[1] if r[1] is not None else 0 for r in result]
    
    if not subjects or not scores or not any(scores):
        return None
    
    # Clear any existing plots
    plt.clf()
    
    # Create bar chart
    fig = plt.figure(figsize=(10, 6))
    plt.bar(range(len(subjects)), scores)
    plt.title('Subject-wise Top Scores')
    plt.xlabel('Subjects')
    plt.ylabel('Top Score')
    plt.xticks(range(len(subjects)), subjects, rotation=45)
    plt.tight_layout()
    
    # Save chart
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filepath = os.path.join(ADMIN_CHARTS_DIR, f'subject_scores_{timestamp}.png')
    plt.savefig(filepath)
    plt.close(fig)
    
    return os.path.basename(filepath)

def generate_admin_subject_attempts():
    """Generate pie chart for subject-wise user attempts"""
    # Get subject-wise attempt counts
    result = db.session.query(
        Subject.name,
        func.count(Scores.id).label('attempt_count')
    ).join(
        Chapter, Subject.id == Chapter.subject_id
    ).join(
        Quiz, Chapter.id == Quiz.chapter_id
    ).join(
        Scores, Quiz.id == Scores.quiz_id
    ).group_by(
        Subject.name
    ).all()
    
    if not result:
        return None
    
    subjects = [r[0] for r in result]
    attempts = [r[1] if r[1] is not None else 0 for r in result]
    
    if not subjects or not attempts or sum(attempts) == 0:
        return None
    
    # Clear any existing plots
    plt.clf()
    
    # Create pie chart
    fig = plt.figure(figsize=(10, 8))
    plt.pie(attempts, labels=subjects, autopct='%1.1f%%')
    plt.axis('equal')
    plt.tight_layout()
    
    # Save chart
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filepath = os.path.join(ADMIN_CHARTS_DIR, f'subject_attempts_{timestamp}.png')
    plt.savefig(filepath)
    plt.close(fig)
    
    return os.path.basename(filepath)

def generate_user_subject_questions():
    """Generate bar chart for subject-wise number of questions"""
    # Get subject-wise question counts
    result = db.session.query(
        Subject.name,
        func.count(Questions.id).label('question_count')
    ).join(
        Chapter, Subject.id == Chapter.subject_id
    ).join(
        Quiz, Chapter.id == Quiz.chapter_id
    ).join(
        Questions, Quiz.id == Questions.quiz_id
    ).group_by(
        Subject.name
    ).all()
    
    if not result:
        return None
    
    subjects = [r[0] for r in result]
    counts = [r[1] if r[1] is not None else 0 for r in result]
    
    if not subjects or not counts or not any(counts):
        return None
    
    # Clear any existing plots
    plt.clf()
    
    # Create bar chart
    fig = plt.figure(figsize=(10, 6))
    plt.bar(range(len(subjects)), counts)
    plt.title('Subject-wise Number of Questions')
    plt.xlabel('Subjects')
    plt.ylabel('Number of Questions')
    plt.xticks(range(len(subjects)), subjects, rotation=45)
    plt.tight_layout()
    
    # Save chart
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filepath = os.path.join(USER_CHARTS_DIR, f'subject_questions_{timestamp}.png')
    plt.savefig(filepath)
    plt.close(fig)
    
    return os.path.basename(filepath)

def generate_user_subject_attempts(user_id):
    """Generate pie chart for subject-wise user attempts for current user"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filepath = os.path.join(USER_CHARTS_DIR, f'user_attempts_{timestamp}.png')
    
    # Get subject-wise attempt counts for the user
    result = db.session.query(
        Subject.name,
        func.count(Scores.id).label('attempt_count')
    ).join(
        Chapter, Subject.id == Chapter.subject_id
    ).join(
        Quiz, Chapter.id == Quiz.chapter_id
    ).join(
        Scores, Quiz.id == Scores.quiz_id
    ).filter(
        Scores.user_id == user_id
    ).group_by(
        Subject.name
    ).all()
    
    if not result:
        return None
    
    subjects = [r[0] for r in result]
    attempts = [r[1] if r[1] is not None else 0 for r in result]
    
    if not subjects or not attempts or sum(attempts) == 0:
        return None
    
    # Clear any existing plots
    plt.clf()
    
    # Create pie chart
    fig = plt.figure(figsize=(10, 8))
    plt.pie(attempts, labels=subjects, autopct='%1.1f%%')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close(fig)
    
    return os.path.basename(filepath)