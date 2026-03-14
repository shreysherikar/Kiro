"""
Netlify serverless function entry point for InspireHer Flask app.
"""

import sys
import os

# Project root is 3 levels up from netlify/functions/app/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

import serverless_wsgi
from app import app
from models import db
from seed import seed_quotes

# Use /tmp for SQLite (only writable dir in Netlify Functions)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/inspireher.db'

with app.app_context():
    db.create_all()

seed_quotes(app)


def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
