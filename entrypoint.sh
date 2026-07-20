#!/bin/sh

echo "Waiting for PostgreSQL to start..."
# Optional: Add nc or pg_isready wait here if necessary

echo "Running Database Migrations..."
python -m alembic upgrade head

echo "Starting FastAPI Server..."
exec "$@"
