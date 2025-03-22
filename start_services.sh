#!/bin/bash

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

redis-server &
mailhog &
celery -A workers.celery worker --loglevel=info &
celery -A workers.celery beat --loglevel=info &

export FLASK_APP=app.py
export FLASK_DEBUG=1
python -m flask run

cleanup() {
    pkill -f "redis-server"
    pkill -f "mailhog"
    pkill -f "celery"
    pkill -f "flask"
    exit 0
}

trap cleanup INT TERM

wait