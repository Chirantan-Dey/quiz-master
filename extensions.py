from flask_sqlalchemy import SQLAlchemy
from flask_security import Security
from flask_caching import Cache

db = SQLAlchemy()

# Initialize cache with default config, will be updated in app.py
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 1
})