"""
Unit tests for S3 upload service.
"""
import pytest
from io import BytesIO
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError, NoCredentialsError
from s3_service import upload_to_s3


@pytest.fixture
def mock_file():
    """Create a mock file object for testing."""
    file = Mock()
    file.filename = 'test_image.jpg'
    file.content_type = 'image/jpeg'
    file.read = Mock(return_value=b'fake image data')
    return file


def test_upload_to_s3_success(mock_file):
    """Test successful file upload to S3."""
    with patch('s3_service.boto3.client') as mock_boto_client:
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        result = upload_to_s3(mock_file, 'inspireher-demo-images')
        
        # Verify S3 client was created with correct region
        mock_boto_client.assert_called_once_with('s3', region_name='us-east-1')
        
        # Verify upload was called
        mock_s3.upload_fileobj.assert_called_once()
        
        # Verify URL format
        assert result is not None
        assert result.startswith('https://inspireher-demo-images.s3.us-east-1.amazonaws.com/')
        assert 'test_image.jpg' in result


def test_upload_to_s3_no_file():
    """Test upload with no file provided."""
    result = upload_to_s3(None, 'inspireher-demo-images')
    assert result is None


def test_upload_to_s3_no_filename():
    """Test upload with file that has no filename."""
    file = Mock()
    file.filename = ''
    result = upload_to_s3(file, 'inspireher-demo-images')
    assert result is None


def test_upload_to_s3_no_credentials_error(mock_file):
    """Test handling of missing AWS credentials."""
    with patch('s3_service.boto3.client') as mock_boto_client:
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.upload_fileobj.side_effect = NoCredentialsError()
        
        result = upload_to_s3(mock_file, 'inspireher-demo-images')
        
        assert result is None


def test_upload_to_s3_no_such_bucket_error(mock_file):
    """Test handling of non-existent S3 bucket."""
    with patch('s3_service.boto3.client') as mock_boto_client:
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        error_response = {'Error': {'Code': 'NoSuchBucket'}}
        mock_s3.upload_fileobj.side_effect = ClientError(error_response, 'upload_fileobj')
        
        result = upload_to_s3(mock_file, 'non-existent-bucket')
        
        assert result is None


def test_upload_to_s3_client_error(mock_file):
    """Test handling of generic S3 ClientError."""
    with patch('s3_service.boto3.client') as mock_boto_client:
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        error_response = {'Error': {'Code': 'AccessDenied'}}
        mock_s3.upload_fileobj.side_effect = ClientError(error_response, 'upload_fileobj')
        
        result = upload_to_s3(mock_file, 'inspireher-demo-images')
        
        assert result is None


def test_upload_to_s3_unexpected_error(mock_file):
    """Test handling of unexpected exceptions."""
    with patch('s3_service.boto3.client') as mock_boto_client:
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.upload_fileobj.side_effect = Exception('Unexpected error')
        
        result = upload_to_s3(mock_file, 'inspireher-demo-images')
        
        assert result is None


def test_upload_to_s3_unique_filename(mock_file):
    """Test that uploaded files get unique filenames."""
    with patch('s3_service.boto3.client') as mock_boto_client:
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Upload the same file twice
        result1 = upload_to_s3(mock_file, 'inspireher-demo-images')
        result2 = upload_to_s3(mock_file, 'inspireher-demo-images')
        
        # Both should succeed
        assert result1 is not None
        assert result2 is not None
        
        # URLs should be different (unique UUIDs)
        assert result1 != result2
