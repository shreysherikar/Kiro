"""
Tests for the home route implementation.

Validates that the / route correctly renders the home page.
"""

import pytest
from app import app
from models import db


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_home_route_exists(client):
    """Test that the / route exists and returns 200 status."""
    response = client.get('/')
    assert response.status_code == 200
