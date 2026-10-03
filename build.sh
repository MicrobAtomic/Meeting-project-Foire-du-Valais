#!/usr/bin/env bash
# Render build: dependencies, static files, schema, demo data (only when the database is empty).
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py seed_demo --if-empty
