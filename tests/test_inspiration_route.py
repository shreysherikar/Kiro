"""
Tests for the inspiration wall route implementation.

Validates that the /inspiration route correctly queries all Quote records
and passes them to the template.
"""

import pytest
from app import app
from models import db, Quote


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


def test_inspiration_route_exists(client):
    """Test that the /inspiration route exists and returns 200 status."""
    response = client.get('/inspiration')
    assert response.status_code == 200


def test_inspiration_queries_all_quotes(client):
    """Test that the inspiration route queries all Quote records."""
    with app.app_context():
        # Create test quotes
        quote1 = Quote(text="The best way to predict the future is to invent it.")
        quote2 = Quote(text="Code is poetry.")
        db.session.add(quote1)
        db.session.add(quote2)
        db.session.commit()
    
    # Query the inspiration route
    response = client.get('/inspiration')
    
    # Verify response is successful
    assert response.status_code == 200
    
    # Verify both quotes are in the response
    response_data = response.data.decode('utf-8')
    assert "The best way to predict the future is to invent it." in response_data
    assert "Code is poetry." in response_data


def test_inspiration_with_no_quotes(client):
    """Test that the inspiration route works when no quotes exist."""
    response = client.get('/inspiration')
    assert response.status_code == 200
    
    # Verify empty state message is shown
    response_data = response.data.decode('utf-8')
    assert "No quotes available yet" in response_data
