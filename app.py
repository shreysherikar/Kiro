"""
InspireHer Women in Tech Inspiration Hub

Main Flask application file that initializes the app, configures database
and AWS S3 settings, and sets up the application context.
"""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import boto3
from models import db, init_db, WomenProfile, Quote
from s3_service import upload_to_s3
from seed import seed_quotes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# ============================================================================
# Database Configuration
# ============================================================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inspireher.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret key for flash messages
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ============================================================================
# AWS S3 Configuration
# ============================================================================
# AWS credentials (should be set via environment variables in production)
app.config['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID', '')
app.config['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY', '')

# S3 bucket configuration
app.config['S3_BUCKET_NAME'] = 'inspireher-demo-images'
app.config['AWS_REGION'] = 'us-east-1'

# ============================================================================
# File Upload Configuration
# ============================================================================
# Set maximum file upload size to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Allowed image file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# Initialize Extensions
# ============================================================================
# Initialize SQLAlchemy with app
db.init_app(app)

# Initialize boto3 S3 client
s3_client = None
try:
    s3_client = boto3.client(
        's3',
        region_name=app.config['AWS_REGION'],
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
    )
    logger.info("S3 client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize S3 client: {str(e)}")
    # App can still run without S3, but image uploads will fail

# ============================================================================
# Routes
# ============================================================================

@app.route('/')
def home():
    """
    Home page route that displays the platform introduction.
    
    Returns:
        Rendered home.html template
    
    Validates: Requirement 1.3 - Serve home page at root endpoint
    """
    return render_template('home.html')


@app.route('/gallery')
def gallery():
    """
    Gallery page route that displays all women profiles.
    
    Queries all WomenProfile records from the database and passes them
    to the gallery.html template for rendering as profile cards.
    
    Returns:
        Rendered gallery.html template with profiles data
    
    Validates: Requirements 2.1, 6.4 - Display all profiles in gallery
    """
    profiles = WomenProfile.query.all()
    return render_template('gallery.html', profiles=profiles)


@app.route('/inspiration')
def inspiration():
    """
    Inspiration wall page route that displays all motivational quotes.
    
    Queries all Quote records from the database and passes them
    to the inspiration.html template for rendering.
    
    Returns:
        Rendered inspiration.html template with quotes data
    
    Validates: Requirements 3.1, 6.5 - Display all quotes on inspiration wall
    """
    quotes = Quote.query.all()
    return render_template('inspiration.html', quotes=quotes)


@app.route('/submit', methods=['GET', 'POST'])
def submit_form():
    """
    Submit form page route that displays and processes the profile submission form.
    
    GET: Renders the submit.html template where users can submit new women profiles
    POST: Processes form submission with validation, image upload, and database storage
    
    Returns:
        GET: Rendered submit.html template
        POST: Redirect to gallery on success, or rendered form with error message
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """
    if request.method == 'POST':
        # Extract form data
        name = request.form.get('name', '').strip()
        field = request.form.get('field', '').strip()
        achievement = request.form.get('achievement', '').strip()
        
        # Validate required fields
        if not name or not field or not achievement:
            error_message = "All fields (name, field, achievement) are required."
            return render_template('submit.html', error=error_message, 
                                 name=name, field=field, achievement=achievement), 400
        
        # Handle image upload if provided
        image_url = None
        if 'image' in request.files:
            image_file = request.files['image']
            
            # Check if a file was actually selected
            if image_file and image_file.filename:
                # Sanitize filename
                safe_filename = secure_filename(image_file.filename)
                
                # Validate file type
                if not allowed_file(safe_filename):
                    error_message = "Invalid file type. Please upload an image."
                    return render_template('submit.html', error=error_message,
                                         name=name, field=field, achievement=achievement), 400
                
                # Upload to S3
                image_url = upload_to_s3(
                    image_file, 
                    app.config['S3_BUCKET_NAME'],
                    app.config['AWS_REGION']
                )
                
                # Check if S3 upload failed
                if image_url is None:
                    error_message = "Image upload failed. Please try again."
                    return render_template('submit.html', error=error_message,
                                         name=name, field=field, achievement=achievement), 500
        
        # Create new WomenProfile record
        try:
            new_profile = WomenProfile(
                name=name,
                field=field,
                achievement=achievement,
                image_url=image_url
            )
            
            # Add to database and commit
            db.session.add(new_profile)
            db.session.commit()
            
            logger.info(f"New profile created successfully: {name}")
            
            # Redirect to gallery on success
            return redirect(url_for('gallery'))
            
        except Exception as e:
            # Rollback on database error
            db.session.rollback()
            logger.error(f"Database error during profile creation: {str(e)}")
            error_message = "Database error. Please try again later."
            return render_template('submit.html', error=error_message,
                                 name=name, field=field, achievement=achievement), 500
    
    # GET request - display form
    return render_template('submit.html')


# ============================================================================
# Error Handlers
# ============================================================================

@app.route('/delete/<int:profile_id>', methods=['POST'])
def delete_profile(profile_id):
    """Delete a profile by ID and redirect back to gallery."""
    profile = WomenProfile.query.get_or_404(profile_id)
    try:
        db.session.delete(profile)
        db.session.commit()
        logger.info(f"Profile deleted: {profile.name}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting profile: {str(e)}")
    return redirect(url_for('gallery'))


@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found errors with a custom page."""
    logger.warning(f"404 Not Found: {request.url}")
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 Internal Server Error with a custom page."""
    logger.error(f"500 Internal Server Error: {str(e)}")
    return render_template('500.html'), 500


@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 Method Not Allowed errors."""
    logger.warning(f"405 Method Not Allowed: {request.method} {request.url}")
    return render_template('405.html'), 405


@app.errorhandler(413)
def request_entity_too_large(e):
    """Handle 413 Request Entity Too Large (file upload too big)."""
    logger.warning(f"413 Request Entity Too Large: {request.url}")
    return render_template('413.html'), 413


if __name__ == '__main__':
    # Initialize database on startup
    init_db(app)

    # Seed initial quotes if none exist
    seed_quotes(app)

    # Run Flask development server
    logger.info("Starting InspireHer application on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
