import os
import matplotlib
matplotlib.use('Agg')  # Required for server-side rendering
import matplotlib.pyplot as plt
from models import Subject, Chapter, Quiz, Questions, Scores, db
from sqlalchemy import func, text
from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple, List, Dict
import seaborn as sns
from functools import lru_cache
import numpy as np
import io

# Configure logging
logger = logging.getLogger(__name__)

# Chart configuration
CHARTS_DIR = os.path.join('static', 'charts')
ADMIN_CHARTS_DIR = os.path.join(CHARTS_DIR, 'admin')
USER_CHARTS_DIR = os.path.join(CHARTS_DIR, 'user')
CHART_CACHE_DURATION = 300  # 5 minutes

# Chart style configuration
STYLE_CONFIG = {
    'light': {
        'background': 'white',
        'text': 'black',
        'grid': '#E5E5E5',
        'colors': sns.color_palette('husl', 8)
    },
    'dark': {
        'background': '#2D2D2D',
        'text': 'white',
        'grid': '#404040',
        'colors': sns.color_palette('husl', 8)
    }
}

def setup_chart_directories():
    """Create chart directories if they don't exist"""
    for directory in [CHARTS_DIR, ADMIN_CHARTS_DIR, USER_CHARTS_DIR]:
        os.makedirs(directory, exist_ok=True)

def cleanup_old_charts(max_age_hours: int = 24):
    """Delete charts older than specified hours"""
    logger.info(f"Cleaning up charts older than {max_age_hours} hours")
    now = datetime.now()
    count = 0
    
    for directory in [ADMIN_CHARTS_DIR, USER_CHARTS_DIR]:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            try:
                # Get file's last modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if now - mtime > timedelta(hours=max_age_hours):
                    os.remove(filepath)
                    count += 1
            except Exception as e:
                logger.error(f"Error processing {filepath}: {str(e)}")
    
    logger.info(f"Cleaned up {count} old chart files")

def apply_chart_style(theme: str = 'light'):
    """Apply consistent style to charts"""
    style = STYLE_CONFIG[theme]
    plt.style.use('seaborn')
    
    params = {
        'figure.facecolor': style['background'],
        'axes.facecolor': style['background'],
        'axes.edgecolor': style['text'],
        'axes.labelcolor': style['text'],
        'text.color': style['text'],
        'xtick.color': style['text'],
        'ytick.color': style['text'],
        'grid.color': style['grid'],
        'figure.autolayout': True,
    }
    plt.rcParams.update(params)
    return style['colors']

def get_chart_size(data_length: int) -> Tuple[int, int]:
    """Determine appropriate chart size based on data"""
    base_width = 10
    base_height = 6
    
    if data_length > 10:
        base_width = 12
        base_height = 8
    elif data_length > 5:
        base_width = 10
        base_height = 7
        
    return base_width, base_height

@lru_cache(maxsize=32)
def get_subject_data(user_id: Optional[int] = None) -> Dict:
    """Get cached subject data for charts"""
    query = text("""
        SELECT 
            s.name as subject_name,
            COUNT(DISTINCT q.id) as quiz_count,
            COUNT(DISTINCT qu.id) as question_count,
            COUNT(DISTINCT sc.id) as attempt_count,
            COALESCE(AVG(sc.total_scored), 0) as avg_score,
            COALESCE(MAX(sc.total_scored), 0) as top_score
        FROM subjects s
        LEFT JOIN chapters c ON s.id = c.subject_id
        LEFT JOIN quizzes q ON c.id = q.chapter_id
        LEFT JOIN questions qu ON q.id = qu.quiz_id
        LEFT JOIN scores sc ON q.id = sc.quiz_id
        WHERE (:user_id IS NULL OR sc.user_id = :user_id)
        GROUP BY s.name
    """)
    
    result = db.session.execute(query, {'user_id': user_id}).fetchall()
    return {row.subject_name: dict(row) for row in result}

def save_chart(fig: plt.Figure, directory: str, prefix: str) -> str:
    """Save chart with proper error handling"""
    try:
        # Save to memory first to avoid partial files
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        
        # Generate filename and path
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'{prefix}_{timestamp}.png'
        filepath = os.path.join(directory, filename)
        
        # Save to file
        with open(filepath, 'wb') as f:
            f.write(buf.getvalue())
        
        return os.path.basename(filepath)
    except Exception as e:
        logger.error(f"Error saving chart: {str(e)}")
        return None
    finally:
        plt.close(fig)

def generate_admin_subject_scores(theme: str = 'light') -> Optional[str]:
    """Generate enhanced bar chart for subject-wise top scores"""
    try:
        data = get_subject_data()
        if not data:
            return None

        subjects = list(data.keys())
        scores = [d['top_score'] for d in data.values()]
        
        colors = apply_chart_style(theme)
        width, height = get_chart_size(len(subjects))
        
        fig = plt.figure(figsize=(width, height))
        ax = fig.add_subplot(111)
        
        bars = ax.bar(range(len(subjects)), scores, color=colors)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}%', ha='center', va='bottom')
        
        plt.title('Subject-wise Top Scores', pad=20)
        plt.xlabel('Subjects', labelpad=10)
        plt.ylabel('Top Score (%)', labelpad=10)
        plt.xticks(range(len(subjects)), subjects, rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        
        return save_chart(fig, ADMIN_CHARTS_DIR, 'subject_scores')
    except Exception as e:
        logger.error(f"Error generating admin subject scores chart: {str(e)}")
        return None

def generate_admin_subject_attempts(theme: str = 'light') -> Optional[str]:
    """Generate enhanced pie chart for subject-wise attempts"""
    try:
        data = get_subject_data()
        if not data:
            return None

        subjects = list(data.keys())
        attempts = [d['attempt_count'] for d in data.values()]
        
        colors = apply_chart_style(theme)
        width, height = get_chart_size(len(subjects))
        
        fig = plt.figure(figsize=(width, height))
        plt.pie(attempts, labels=subjects, autopct='%1.1f%%', colors=colors,
               shadow=True, startangle=90)
        plt.title('Subject-wise Attempt Distribution', pad=20)
        
        return save_chart(fig, ADMIN_CHARTS_DIR, 'subject_attempts')
    except Exception as e:
        logger.error(f"Error generating admin subject attempts chart: {str(e)}")
        return None

def generate_user_subject_questions(theme: str = 'light') -> Optional[str]:
    """Generate enhanced bar chart for subject-wise questions"""
    try:
        data = get_subject_data()
        if not data:
            return None

        subjects = list(data.keys())
        counts = [d['question_count'] for d in data.values()]
        
        colors = apply_chart_style(theme)
        width, height = get_chart_size(len(subjects))
        
        fig = plt.figure(figsize=(width, height))
        ax = fig.add_subplot(111)
        
        bars = ax.bar(range(len(subjects)), counts, color=colors)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   str(int(height)), ha='center', va='bottom')
        
        plt.title('Questions Available by Subject', pad=20)
        plt.xlabel('Subjects', labelpad=10)
        plt.ylabel('Number of Questions', labelpad=10)
        plt.xticks(range(len(subjects)), subjects, rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        
        return save_chart(fig, USER_CHARTS_DIR, 'subject_questions')
    except Exception as e:
        logger.error(f"Error generating user subject questions chart: {str(e)}")
        return None

def generate_user_subject_attempts(user_id: int, theme: str = 'light') -> Optional[str]:
    """Generate enhanced progress chart for user attempts"""
    try:
        data = get_subject_data(user_id)
        if not data:
            return None

        subjects = list(data.keys())
        attempts = [d['attempt_count'] for d in data.values()]
        scores = [d['avg_score'] for d in data.values()]
        
        colors = apply_chart_style(theme)
        width, height = get_chart_size(len(subjects))
        
        fig = plt.figure(figsize=(width, height))
        ax = fig.add_subplot(111)
        
        # Create grouped bars
        x = np.arange(len(subjects))
        width = 0.35
        
        ax.bar(x - width/2, attempts, width, label='Attempts', color=colors[0])
        ax.bar(x + width/2, scores, width, label='Avg Score (%)', color=colors[1])
        
        plt.title('Your Progress by Subject', pad=20)
        plt.xlabel('Subjects', labelpad=10)
        plt.ylabel('Count / Score', labelpad=10)
        plt.xticks(x, subjects, rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        return save_chart(fig, USER_CHARTS_DIR, f'user_attempts_{user_id}')
    except Exception as e:
        logger.error(f"Error generating user subject attempts chart: {str(e)}")
        return None

# Initialize on module load
setup_chart_directories()
cleanup_old_charts()