"""
Netlify Serverless Function Handler for Group No1 Flask Application.
Routes incoming HTTP requests to Flask via serverless-wsgi.
"""

import sys
from pathlib import Path

# Add project root and group-no1 to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "group-no1"))

import serverless_wsgi
from app import create_app
from app.extensions import db

# Create production app instance
app = create_app("production")

# Ensure tables exist on cold start
with app.app_context():
    try:
        db.create_all()
    except Exception as exc:
        print(f"Warning: Database initialization exception on Netlify cold start: {exc}")


def handler(event, context):
    """Serverless Lambda handler for Netlify."""
    return serverless_wsgi.handle_request(app, event, context)
