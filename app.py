from flask import Flask, jsonify
from extensions import db, cache, celery, init_celery
import views
import create_initial_data
import resources
from flask_security import auth_required, Security, current_user
from celery.schedules import crontab
from datetime import datetime, UTC
from flask_wtf.csrf import CSRFProtect, generate_csrf

class Config:
    # Flask Core
    DEBUG = True
    SECRET_KEY = 'NbrKrOgSTkiVDItpfQzjF6UuX0jNJcuwTKX6MypiCJQ'
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECURITY_PASSWORD_SALT = '9RrPTYTgV4c-iFafQeB7RQ'
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'
    WTF_CSRF_CHECK_DEFAULT = False  # Let Flask-Security handle CSRF
    SECURITY_CSRF_PROTECT_MECHANISMS = ['session', 'token']
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True  # Allow login without CSRF
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # Redis & Cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 1
    
    # Celery
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_TIMEZONE = 'Asia/Kolkata'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_TIME_LIMIT = 30 * 60
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
    CELERY_BROKER_CONNECTION_RETRY = True
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
    CELERY_BROKER_CONNECTION_MAX_RETRIES = 3
    
    # Celery Beat Schedule
    CELERYBEAT_SCHEDULE = {
        'daily-reminder': {
            'task': 'workers.send_daily_reminder',
            'schedule': crontab(hour=18, minute=0),  # 6 PM IST
        },
        'monthly-report': {
            'task': 'workers.send_monthly_report',
            'schedule': crontab(0, 0, day_of_month='1'),  # First day of every month at midnight
        }
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific settings here if needed

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Initialize Celery
    init_celery(app)

    # Setup CORS
    CORS(
        app,
        resources={
            r"/*": {
                "origins": app.config['CORS_ORIGINS'],
                "methods": app.config['CORS_METHODS'],
                "allow_headers": app.config['CORS_ALLOW_HEADERS']
            }
        }
    )

    # Setup security headers
    Talisman(
        app,
        force_https=app.config['SESSION_COOKIE_SECURE'],
        session_cookie_secure=app.config['SESSION_COOKIE_SECURE'],
        frame_options='DENY',
        content_security_policy=app.config['CSP']
    )

    # Setup rate limiting
    Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[app.config['RATELIMIT_DEFAULT']]
    )

    # Setup monitoring
    metrics = PrometheusMetrics(app)
    metrics.info('app_info', 'Application info', version='1.0.0')

    # Setup Sentry if configured
    if app.config['SENTRY_DSN']:
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )

    with app.app_context():
        from models import User, Role
        from flask_security import SQLAlchemyUserDatastore

        user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        security = Security(app, user_datastore)
        
        db.create_all()
        create_initial_data.create_data(user_datastore)
        
    # enable CSRF protection
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True
    app.config['SECURITY_CSRF_PROTECT_MECHANISMS'] = ['session', 'token']
    app.config['SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS'] = False

    # setup the view
    views.create_views(app, user_datastore, db)

    # setup api
    resources.api.init_app(app)

        # Update last visit timestamp for authenticated users
        @app.before_request
        def update_last_visit():
            if current_user.is_authenticated:
                current_user.last_visit = datetime.now(UTC)
                db.session.commit()

        # Add CSRF token to all responses
        @app.after_request
        def add_csrf_token(response):
            if current_user.is_authenticated:
                response.headers['X-CSRF-Token'] = generate_csrf()
            return response

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
