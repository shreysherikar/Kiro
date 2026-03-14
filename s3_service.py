"""
S3 Service Module for InspireHer Application

This module provides functionality for uploading files to AWS S3.
It handles file uploads with unique filename generation and error handling.
"""

import uuid
import logging
from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_to_s3(file, bucket_name, aws_region='us-east-1'):
    """
    Upload a file to AWS S3 bucket with unique filename generation.
    
    This function takes a file object, generates a unique filename using UUID,
    and uploads it to the specified S3 bucket. It handles various AWS exceptions
    and returns the public S3 URL on success.
    
    Args:
        file: File object from Flask request (werkzeug.datastructures.FileStorage)
        bucket_name: Name of the S3 bucket (e.g., 'inspireher-demo-images')
        aws_region: AWS region for the bucket (default: 'us-east-1')
    
    Returns:
        str: S3 URL of the uploaded file on success
        None: On failure (with error logged)
    
    Raises:
        None: All exceptions are caught and logged
    
    Example:
        >>> from flask import request
        >>> file = request.files['image']
        >>> url = upload_to_s3(file, 'inspireher-demo-images')
        >>> if url:
        ...     print(f"File uploaded: {url}")
    """
    if not file or not file.filename:
        logger.error("No file provided or file has no filename")
        return None
    
    try:
        # Sanitize the original filename
        original_filename = secure_filename(file.filename)
        
        # Generate unique filename using UUID to prevent collisions
        unique_filename = f"{uuid.uuid4()}-{original_filename}"
        
        # Initialize S3 client
        s3_client = boto3.client('s3', region_name=aws_region)
        
        # Upload file to S3
        s3_client.upload_fileobj(
            file,
            bucket_name,
            unique_filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        # Construct the public S3 URL
        s3_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{unique_filename}"
        
        logger.info(f"File uploaded successfully to S3: {s3_url}")
        return s3_url
        
    except NoCredentialsError:
        logger.error("AWS credentials not found or invalid")
        return None
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        
        if error_code == 'NoSuchBucket':
            logger.error(f"S3 bucket '{bucket_name}' does not exist")
        else:
            logger.error(f"S3 ClientError during upload: {error_code} - {str(e)}")
        
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error during S3 upload: {str(e)}")
        return None
