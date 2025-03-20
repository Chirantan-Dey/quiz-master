from flask_sqlalchemy import SQLAlchemy
from flask_security import Security
from flask_caching import Cache
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()

# Initialize cache with Redis db 0
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 1
})