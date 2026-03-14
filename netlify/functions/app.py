"""
Netlify serverless function entry point for InspireHer Flask app.
Uses serverless-wsgi to wrap the Flask WSGI app as a Lambda-compatible handler.
"""

import sys
import os

# Add bundled dependencies and project root to path
base = os.path.dirname(__file__)
sys.path.insert(0, base)                        # netlify/functions (bundled deps land here)
sys.path.insert(0, os.path.join(base, '..', '..'))  # project root

import serverless_wsgi
from app import app, init_db, seed_quotes

# Use /tmp for SQLite since Netlify Functions filesystem is read-only except /tmp
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/inspireher.db'

# Initialize DB and seed on cold start
with app.app_context():
    from models import db
    db.create_all()

seed_quotes(app)


def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
