# S3 Service Usage Guide

## Overview
The `s3_service.py` module provides the `upload_to_s3()` function for uploading files to AWS S3 with automatic unique filename generation.

## Function Signature
```python
upload_to_s3(file, bucket_name, aws_region='us-east-1')
```

## Parameters
- `file`: File object from Flask request (werkzeug.datastructures.FileStorage)
- `bucket_name`: Name of the S3 bucket (e.g., 'inspireher-demo-images')
- `aws_region`: AWS region for the bucket (default: 'us-east-1')

## Returns
- `str`: S3 URL of the uploaded file on success
- `None`: On failure (error is logged)

## Usage Example

```python
from flask import Flask, request
from s3_service import upload_to_s3

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return 'No file provided', 400
    
    file = request.files['image']
    
    # Upload to S3
    s3_url = upload_to_s3(file, 'inspireher-demo-images')
    
    if s3_url:
        return {'url': s3_url}, 200
    else:
        return 'Upload failed', 500
```

## Features
- ✅ Unique filename generation using UUID
- ✅ Filename sanitization with werkzeug.secure_filename
- ✅ Comprehensive error handling (NoCredentialsError, ClientError, NoSuchBucket)
- ✅ Proper logging for debugging
- ✅ Returns None on any failure
- ✅ Sets correct ContentType for uploaded files

## Error Handling
The function handles the following error scenarios:
- Missing or empty file
- AWS credentials not found (NoCredentialsError)
- S3 bucket doesn't exist (NoSuchBucket)
- Other S3 client errors (ClientError)
- Unexpected exceptions

All errors are logged and the function returns `None`.

## AWS Configuration
Ensure AWS credentials are configured via:
- Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- AWS credentials file (~/.aws/credentials)
- IAM role (for EC2/ECS deployments)

## Testing
Run the test suite:
```bash
pytest tests/test_s3_service.py -v
```
