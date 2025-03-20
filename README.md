# Quiz Master

A modern quiz management system built with Flask and Vue.js, featuring automated scheduling, interactive analytics, and comprehensive performance tracking.

## Features

- **Quiz Management**: Create, edit, and manage quizzes with ease
- **Interactive Analytics**: Real-time performance tracking and visualizations
- **Offline Support**: Continue taking quizzes even without internet
- **Automated Scheduling**: Daily reminders and monthly reports
- **Responsive Design**: Works seamlessly on all devices
- **Dark/Light Themes**: User-friendly interface with theme support
- **Accessibility**: WCAG compliant with keyboard navigation

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- Redis
- MailHog (for email testing)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/quiz-master.git
   cd quiz-master
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Setup environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize database:
   ```bash
   flask db upgrade
   python create_initial_data.py
   ```

### Running the Application

1. Start Redis:
   ```bash
   redis-server
   ```

2. Start Celery worker:
   ```bash
   celery -A workers worker --loglevel=info
   ```

3. Start Celery beat:
   ```bash
   celery -A workers beat --loglevel=info
   ```

4. Start MailHog:
   ```bash
   mailhog
   ```

5. Run the application:
   ```bash
   ./run.sh
   ```

## API Documentation

### Authentication

All protected endpoints require:
- `Authentication-Token` header with valid token
- `X-CSRF-Token` header for POST/PUT/DELETE requests

### Endpoints

#### Users and Authentication
- `POST /`: Login
- `POST /register`: Register new user
- `POST /logout`: Logout

#### Quiz Management
- `GET /api/quizzes`: List quizzes
- `POST /api/quizzes`: Create quiz
- `PUT /api/quizzes/<id>`: Update quiz
- `DELETE /api/quizzes/<id>`: Delete quiz

#### Questions
- `GET /api/questions`: List questions
- `POST /api/questions`: Create question
- `PUT /api/questions/<id>`: Update question
- `DELETE /api/questions/<id>`: Delete question

#### Scores
- `GET /api/scores`: Get user scores
- `POST /api/scores`: Submit quiz score

#### Analytics
- `GET /api/charts/admin`: Get admin analytics
- `GET /api/charts/user`: Get user analytics

## Development

### Project Structure
```
quiz-master/
├── app.py              # Flask application
├── models.py           # Database models
├── views.py           # View functions
├── resources.py       # API resources
├── workers.py         # Celery tasks
├── charts.py          # Chart generation
├── static/
│   ├── components/    # Vue components
│   ├── pages/         # Vue pages
│   └── utils/         # Frontend utilities
└── templates/
    ├── index.html     # Main template
    └── emails/        # Email templates
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_api.py
```

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Lint code
flake8
```

## Deployment

### Production Setup

1. Update production settings:
   ```bash
   export FLASK_ENV=production
   export FLASK_CONFIG=production
   ```

2. Configure web server (nginx example):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. Set up SSL with Let's Encrypt:
   ```bash
   certbot --nginx -d your-domain.com
   ```

4. Configure supervisor for process management:
   ```ini
   [program:quizmaster]
   command=/path/to/venv/bin/gunicorn -w 4 app:app
   directory=/path/to/quiz-master
   autostart=true
   autorestart=true
   ```

### Monitoring

1. Set up Sentry for error tracking:
   ```python
   sentry_sdk.init(dsn="your-sentry-dsn")
   ```

2. Configure Prometheus metrics:
   ```python
   from prometheus_flask_exporter import PrometheusMetrics
   metrics = PrometheusMetrics(app)
   ```

3. Set up logging:
   ```bash
   tail -f logs/app.log
   tail -f logs/celery.log
   ```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask Security for authentication
- Vue.js for frontend framework
- Celery for task queue
- Redis for caching
- MailHog for email testing