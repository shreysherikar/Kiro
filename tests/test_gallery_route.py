"""
Tests for the gallery route implementation.

Validates that the /gallery route correctly queries all WomenProfile records
and passes them to the template.
"""

import pytest
from app import app
from models import db, WomenProfile


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


def test_gallery_route_exists(client):
    """Test that the /gallery route exists and returns 200 status."""
    response = client.get('/gallery')
    assert response.status_code == 200


def test_gallery_queries_all_profiles(client):
    """Test that the gallery route queries all WomenProfile records."""
    with app.app_context():
        # Create test profiles
        profile1 = WomenProfile(
            name="Ada Lovelace",
            field="Computer Science",
            achievement="First computer programmer",
            image_url="https://example.com/ada.jpg"
        )
        profile2 = WomenProfile(
            name="Grace Hopper",
            field="Computer Science",
            achievement="Developed first compiler",
            image_url="https://example.com/grace.jpg"
        )
        db.session.add(profile1)
        db.session.add(profile2)
        db.session.commit()
    
    # Query the gallery route
    response = client.get('/gallery')
    
    # Verify response is successful
    assert response.status_code == 200
    
    # Verify both profiles are in the response
    response_data = response.data.decode('utf-8')
    assert "Ada Lovelace" in response_data
    assert "Grace Hopper" in response_data
    assert "First computer programmer" in response_data
    assert "Developed first compiler" in response_data


def test_gallery_with_no_profiles(client):
    """Test that the gallery route works when no profiles exist."""
    response = client.get('/gallery')
    assert response.status_code == 200
    
    # Verify empty state message is shown
    response_data = response.data.decode('utf-8')
    assert "No profiles available yet" in response_data
