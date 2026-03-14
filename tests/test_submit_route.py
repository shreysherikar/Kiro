"""
Tests for the submit route POST handler implementation.

Validates that the /submit route correctly handles form submissions,
validates required fields, uploads images to S3, creates database records,
and redirects to the gallery on success.
"""

import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from app import app
from models import db, WomenProfile


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['S3_BUCKET_NAME'] = 'test-bucket'
    app.config['AWS_REGION'] = 'us-east-1'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_submit_get_route_exists(client):
    """Test that the GET /submit route exists and returns 200 status."""
    response = client.get('/submit')
    assert response.status_code == 200


def test_submit_post_with_valid_data_no_image(client):
    """Test successful profile submission without image."""
    # Submit form data
    response = client.post('/submit', data={
        'name': 'Ada Lovelace',
        'field': 'Computer Science',
        'achievement': 'First computer programmer'
    }, follow_redirects=False)
    
    # Verify redirect to gallery
    assert response.status_code == 302
    assert '/gallery' in response.location
    
    # Verify database record was created
    with app.app_context():
        profile = WomenProfile.query.filter_by(name='Ada Lovelace').first()
        assert profile is not None
        assert profile.field == 'Computer Science'
        assert profile.achievement == 'First computer programmer'
        assert profile.image_url is None


def test_submit_post_missing_name(client):
    """Test that submission fails when name is missing."""
    response = client.post('/submit', data={
        'name': '',
        'field': 'Computer Science',
        'achievement': 'First computer programmer'
    })
    
    # Verify error response
    assert response.status_code == 400
    response_data = response.data.decode('utf-8')
    assert 'All fields' in response_data or 'required' in response_data
    
    # Verify no database record was created
    with app.app_context():
        count = WomenProfile.query.count()
        assert count == 0


def test_submit_post_missing_field(client):
    """Test that submission fails when field is missing."""
    response = client.post('/submit', data={
        'name': 'Ada Lovelace',
        'field': '',
        'achievement': 'First computer programmer'
    })
    
    # Verify error response
    assert response.status_code == 400
    response_data = response.data.decode('utf-8')
    assert 'All fields' in response_data or 'required' in response_data
    
    # Verify no database record was created
    with app.app_context():
        count = WomenProfile.query.count()
        assert count == 0


def test_submit_post_missing_achievement(client):
    """Test that submission fails when achievement is missing."""
    response = client.post('/submit', data={
        'name': 'Ada Lovelace',
        'field': 'Computer Science',
        'achievement': ''
    })
    
    # Verify error response
    assert response.status_code == 400
    response_data = response.data.decode('utf-8')
    assert 'All fields' in response_data or 'required' in response_data
    
    # Verify no database record was created
    with app.app_context():
        count = WomenProfile.query.count()
        assert count == 0


@patch('app.upload_to_s3')
def test_submit_post_with_image_success(mock_upload, client):
    """Test successful profile submission with image upload."""
    # Mock S3 upload to return a URL
    mock_upload.return_value = 'https://test-bucket.s3.us-east-1.amazonaws.com/test-image.jpg'
    
    # Create a fake image file
    image_data = BytesIO(b'fake image data')
    image_data.name = 'test.jpg'
    
    # Submit form data with image
    response = client.post('/submit', data={
        'name': 'Grace Hopper',
        'field': 'Computer Science',
        'achievement': 'Developed first compiler',
        'image': (image_data, 'test.jpg')
    }, content_type='multipart/form-data', follow_redirects=False)
    
    # Verify redirect to gallery
    assert response.status_code == 302
    assert '/gallery' in response.location
    
    # Verify upload_to_s3 was called
    assert mock_upload.called
    
    # Verify database record was created with S3 URL
    with app.app_context():
        profile = WomenProfile.query.filter_by(name='Grace Hopper').first()
        assert profile is not None
        assert profile.image_url == 'https://test-bucket.s3.us-east-1.amazonaws.com/test-image.jpg'


@patch('app.upload_to_s3')
def test_submit_post_with_image_upload_failure(mock_upload, client):
    """Test that submission fails gracefully when S3 upload fails."""
    # Mock S3 upload to return None (failure)
    mock_upload.return_value = None
    
    # Create a fake image file
    image_data = BytesIO(b'fake image data')
    image_data.name = 'test.jpg'
    
    # Submit form data with image
    response = client.post('/submit', data={
        'name': 'Grace Hopper',
        'field': 'Computer Science',
        'achievement': 'Developed first compiler',
        'image': (image_data, 'test.jpg')
    }, content_type='multipart/form-data')
    
    # Verify error response
    assert response.status_code == 500
    response_data = response.data.decode('utf-8')
    assert 'upload failed' in response_data.lower() or 'try again' in response_data.lower()
    
    # Verify no database record was created
    with app.app_context():
        count = WomenProfile.query.count()
        assert count == 0


def test_submit_post_preserves_form_data_on_error(client):
    """Test that form data is preserved when validation fails."""
    response = client.post('/submit', data={
        'name': 'Ada Lovelace',
        'field': 'Computer Science',
        'achievement': ''  # Missing achievement
    })
    
    # Verify error response
    assert response.status_code == 400
    
    # Verify form data is preserved in response
    response_data = response.data.decode('utf-8')
    assert 'Ada Lovelace' in response_data
    assert 'Computer Science' in response_data


# ============================================================================
# Task 9.4 - Validation Tests
# ============================================================================

def test_submit_all_fields_empty(client):
    """Test that submission fails when all required fields are empty."""
    response = client.post('/submit', data={
        'name': '',
        'field': '',
        'achievement': ''
    })
    assert response.status_code == 400
    response_data = response.data.decode('utf-8')
    assert 'All fields' in response_data or 'required' in response_data

    with app.app_context():
        assert WomenProfile.query.count() == 0


def test_submit_invalid_file_type_rejected(client):
    """Test that uploading a non-image file type is rejected."""
    file_data = BytesIO(b'not an image')
    response = client.post('/submit', data={
        'name': 'Ada Lovelace',
        'field': 'Computer Science',
        'achievement': 'First computer programmer',
        'image': (file_data, 'malware.exe')
    }, content_type='multipart/form-data')

    assert response.status_code == 400
    response_data = response.data.decode('utf-8')
    assert 'Invalid file type' in response_data or 'image' in response_data.lower()

    with app.app_context():
        assert WomenProfile.query.count() == 0


def test_submit_valid_image_types_accepted(client):
    """Test that valid image file types (jpg, png, gif) are accepted."""
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        with app.app_context():
            db.drop_all()
            db.create_all()

        with patch('app.upload_to_s3') as mock_upload:
            mock_upload.return_value = f'https://bucket.s3.amazonaws.com/test.{ext}'
            file_data = BytesIO(b'fake image data')
            response = client.post('/submit', data={
                'name': f'Test User {ext}',
                'field': 'Tech',
                'achievement': 'Achievement',
                'image': (file_data, f'photo.{ext}')
            }, content_type='multipart/form-data', follow_redirects=False)

        assert response.status_code == 302, f"Expected redirect for .{ext} but got {response.status_code}"


def test_submit_invalid_file_type_preserves_form_data(client):
    """Test that form data is preserved when an invalid file type is submitted."""
    file_data = BytesIO(b'not an image')
    response = client.post('/submit', data={
        'name': 'Grace Hopper',
        'field': 'Computer Science',
        'achievement': 'Developed first compiler',
        'image': (file_data, 'document.pdf')
    }, content_type='multipart/form-data')

    assert response.status_code == 400
    response_data = response.data.decode('utf-8')
    assert 'Grace Hopper' in response_data
    assert 'Computer Science' in response_data


def test_404_error_handler(client):
    """Test that navigating to a non-existent route returns a custom 404 page."""
    response = client.get('/this-route-does-not-exist')
    assert response.status_code == 404
    response_data = response.data.decode('utf-8')
    assert '404' in response_data


def test_405_error_handler(client):
    """Test that using the wrong HTTP method returns a 405 response."""
    # The /gallery route only accepts GET; sending POST should return 405
    response = client.post('/gallery')
    assert response.status_code == 405


def test_413_error_handler(client):
    """Test that uploading a file exceeding MAX_CONTENT_LENGTH returns 413."""
    # Temporarily lower the limit to trigger 413
    app.config['MAX_CONTENT_LENGTH'] = 10  # 10 bytes

    large_data = BytesIO(b'x' * 100)
    response = client.post('/submit', data={
        'name': 'Ada',
        'field': 'Tech',
        'achievement': 'Achievement',
        'image': (large_data, 'big.jpg')
    }, content_type='multipart/form-data')

    # Restore limit
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    assert response.status_code == 413
