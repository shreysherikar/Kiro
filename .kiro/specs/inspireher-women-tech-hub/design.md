# Design Document: InspireHer Women in Tech Inspiration Hub

## Overview

InspireHer is a Flask-based web application that celebrates women in technology through a gallery of inspiring profiles and motivational quotes. The system follows a traditional three-tier architecture with a Flask backend, SQLite database for persistence, and server-side rendered HTML templates styled with Tailwind CSS. Images are stored externally in AWS S3 to enable scalability.

The application provides three main user-facing features:
1. A home page introducing the platform
2. A women leaders gallery displaying profile cards with images
3. An inspiration wall showing motivational quotes
4. A submission form for users to contribute new profiles

The design prioritizes simplicity and maintainability, using Flask's built-in templating and routing capabilities, SQLAlchemy ORM for database operations, and boto3 for S3 integration.

## Architecture

### System Architecture

The application follows a monolithic architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│                    (HTML + Tailwind CSS)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Flask Application                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routes     │  │   Models     │  │   Services   │     │
│  │  (Views)     │──│  (SQLAlchemy)│──│  (S3 Upload) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────┬────────────────┬────────────────────────────────┘
             │                │
             ▼                ▼
    ┌────────────────┐  ┌────────────────┐
    │  SQLite DB     │  │   AWS S3       │
    │  (Profiles,    │  │  (Images)      │
    │   Quotes)      │  │                │
    └────────────────┘  └────────────────┘
```

### Technology Stack

- **Backend Framework**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Object Storage**: AWS S3 (via boto3)
- **Frontend**: Jinja2 templates with Tailwind CSS
- **File Upload**: Flask file handling with werkzeug utilities

### Deployment Model

Development deployment runs on localhost:5000. The application is designed as a single-process Flask server suitable for development and small-scale deployment.

## Components and Interfaces

### 1. Flask Application (`app.py`)

The main application module that initializes Flask, configures the database, and registers routes.

**Responsibilities:**
- Initialize Flask app with configuration
- Configure SQLAlchemy database connection
- Set up AWS S3 client with credentials
- Register route handlers
- Initialize database schema on startup

**Configuration:**
- `SQLALCHEMY_DATABASE_URI`: SQLite database file path
- `AWS_ACCESS_KEY_ID`: AWS credentials for S3
- `AWS_SECRET_ACCESS_KEY`: AWS credentials for S3
- `S3_BUCKET_NAME`: `inspireher-demo-images`
- `AWS_REGION`: `us-east-1`

### 2. Database Models (`models.py`)

SQLAlchemy ORM models representing the database schema.

**WomenProfile Model:**
```python
class WomenProfile:
    id: Integer (Primary Key, Auto-increment)
    name: String(100) (Required)
    field: String(100) (Required)
    achievement: Text (Required)
    image_url: String(500) (Optional)
```

**Quote Model:**
```python
class Quote:
    id: Integer (Primary Key, Auto-increment)
    text: Text (Required)
```

### 3. Routes/Views

**Home Route (`/`)**
- Method: GET
- Returns: Rendered home.html template
- Purpose: Display platform introduction

**Gallery Route (`/gallery`)**
- Method: GET
- Returns: Rendered gallery.html with all profiles
- Database Query: `SELECT * FROM women_profiles`
- Purpose: Display all women profiles as cards

**Inspiration Wall Route (`/inspiration`)**
- Method: GET
- Returns: Rendered inspiration.html with all quotes
- Database Query: `SELECT * FROM quotes`
- Purpose: Display motivational quotes

**Submit Route (`/submit`)**
- Method: GET
- Returns: Rendered submit.html with form
- Purpose: Display submission form

**Submit Handler Route (`/submit`)**
- Method: POST
- Input: Form data (name, field, achievement, image file)
- Process:
  1. Validate required fields
  2. Upload image to S3 if provided
  3. Create new WomenProfile record
  4. Commit to database
- Returns: Redirect to /gallery on success, error message on failure
- Purpose: Process profile submission

### 4. S3 Upload Service

**Function: `upload_to_s3(file, bucket_name)`**
- Input: File object from Flask request, S3 bucket name
- Process:
  1. Generate unique filename using UUID
  2. Upload file to S3 using boto3
  3. Construct public URL
- Returns: S3 URL string or None on failure
- Error Handling: Catches boto3 exceptions and returns None

### 5. Templates

**base.html**
- Base template with Tailwind CSS CDN link
- Navigation structure
- Block definitions for content

**home.html**
- Extends base.html
- Displays platform introduction and mission

**gallery.html**
- Extends base.html
- Displays grid of profile cards
- Shows empty state when no profiles exist

**inspiration.html**
- Extends base.html
- Displays list of quotes
- Shows empty state when no quotes exist

**submit.html**
- Extends base.html
- Form with fields: name, field, achievement, image upload
- Client-side validation for required fields

## Data Models

### Database Schema

**Table: women_profiles**
```sql
CREATE TABLE women_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    field VARCHAR(100) NOT NULL,
    achievement TEXT NOT NULL,
    image_url VARCHAR(500)
);
```

**Table: quotes**
```sql
CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL
);
```

### Data Flow

**Profile Submission Flow:**
1. User submits form with profile data and image
2. Flask receives POST request at `/submit`
3. Validate required fields (name, field, achievement)
4. If image provided:
   - Generate unique filename
   - Upload to S3 using boto3
   - Receive S3 URL
5. Create WomenProfile instance with data and S3 URL
6. Save to database via SQLAlchemy
7. Redirect to gallery

**Gallery Display Flow:**
1. User navigates to `/gallery`
2. Flask queries all WomenProfile records
3. Template renders cards with data from database
4. Images loaded from S3 URLs

**Inspiration Wall Flow:**
1. User navigates to `/inspiration`
2. Flask queries all Quote records
3. Template renders quotes in list format

### File Upload Constraints

- Accepted file types: Images (jpg, jpeg, png, gif)
- File size limit: Enforced by Flask configuration (e.g., 16MB)
- Filename sanitization: Use werkzeug.utils.secure_filename
- Unique naming: UUID prefix to prevent collisions

### S3 Storage Structure

```
s3://inspireher-demo-images/
  ├── {uuid}-{original-filename}.jpg
  ├── {uuid}-{original-filename}.png
  └── ...
```

Bucket URL: `https://inspireher-demo-images.s3.us-east-1.amazonaws.com`

Public read access required for image URLs to be accessible in browser.


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Gallery displays all profiles

*For any* set of WomenProfile records in the database, when the gallery page is requested, the response should contain all profile names from the database.

**Validates: Requirements 2.1, 6.4**

### Property 2: Profile cards contain all required information

*For any* WomenProfile record with name, field, achievement, and image_url, when rendered as a card in the gallery, the HTML output should contain all four field values.

**Validates: Requirements 2.2, 2.3**

### Property 3: Inspiration wall displays all quotes

*For any* set of Quote records in the database, when the inspiration wall page is requested, the response should contain all quote texts from the database.

**Validates: Requirements 3.1, 6.5**

### Property 4: Valid profile submission creates database record

*For any* valid profile data (non-empty name, field, and achievement), when submitted through the form, a new WomenProfile record should exist in the database with matching field values.

**Validates: Requirements 4.2, 6.1**

### Property 5: Image upload stores S3 URL in database

*For any* valid image file uploaded with a profile submission, the created WomenProfile record should have an image_url field containing a valid S3 URL (not binary data), and the image should be accessible at that URL.

**Validates: Requirements 4.3, 4.4, 5.1, 5.4**

### Property 6: Unique filename generation

*For any* two different image uploads, the generated filenames stored in S3 should be unique (no collisions).

**Validates: Requirements 5.2**

### Property 7: Invalid submissions rejected

*For any* profile submission with one or more missing required fields (name, field, or achievement), the system should reject the submission, display an error message, and not create a database record.

**Validates: Requirements 4.5**

### Property 8: Successful submission redirects to gallery

*For any* valid profile submission that successfully creates a database record, the HTTP response should be a redirect (status 302 or 303) to the gallery endpoint.

**Validates: Requirements 4.6**

## Error Handling

### Input Validation Errors

**Missing Required Fields:**
- Validation: Check that name, field, and achievement are non-empty strings
- Response: Return form with error message "All fields are required"
- HTTP Status: 400 Bad Request
- User Experience: Form data preserved, error displayed at top

**Invalid File Type:**
- Validation: Check file extension against allowed types (jpg, jpeg, png, gif)
- Response: Return form with error message "Invalid file type. Please upload an image."
- HTTP Status: 400 Bad Request
- User Experience: Form data preserved except file input

**File Too Large:**
- Validation: Flask MAX_CONTENT_LENGTH configuration
- Response: Request Entity Too Large error
- HTTP Status: 413
- User Experience: Display error message with size limit

### S3 Upload Errors

**S3 Connection Failure:**
- Detection: boto3 ClientError or ConnectionError
- Handling: Log error, return user-friendly message
- Response: "Image upload failed. Please try again."
- HTTP Status: 500 Internal Server Error
- Fallback: Profile creation should fail (don't create profile without image if image was provided)

**Invalid AWS Credentials:**
- Detection: boto3 NoCredentialsError or InvalidAccessKeyId
- Handling: Log error with details for administrator
- Response: "Service temporarily unavailable"
- HTTP Status: 503 Service Unavailable

**S3 Bucket Not Found:**
- Detection: boto3 NoSuchBucket error
- Handling: Log error, alert administrator
- Response: "Service temporarily unavailable"
- HTTP Status: 503 Service Unavailable

### Database Errors

**Database Connection Failure:**
- Detection: SQLAlchemy OperationalError
- Handling: Log error, return generic error message
- Response: "Database error. Please try again later."
- HTTP Status: 500 Internal Server Error

**Constraint Violation:**
- Detection: SQLAlchemy IntegrityError
- Handling: Log error, return specific error message
- Response: "Invalid data. Please check your input."
- HTTP Status: 400 Bad Request

**Database Initialization Failure:**
- Detection: Exception during db.create_all()
- Handling: Log error and exit application
- Response: Application fails to start
- Recovery: Administrator must fix database configuration

### Route Errors

**404 Not Found:**
- Trigger: User navigates to non-existent route
- Response: Custom 404 page with navigation back to home
- HTTP Status: 404 Not Found

**405 Method Not Allowed:**
- Trigger: Wrong HTTP method used for endpoint
- Response: Error message indicating allowed methods
- HTTP Status: 405 Method Not Allowed

### General Error Handling Strategy

1. **Catch Specific Exceptions First:** Handle known error types with specific messages
2. **Log All Errors:** Use Python logging to record errors with context
3. **User-Friendly Messages:** Never expose stack traces or technical details to users
4. **Fail Gracefully:** Return user to a safe state (form with data, or home page)
5. **Administrator Alerts:** Log critical errors (S3, database) for monitoring

## Testing Strategy

### Overview

The testing strategy employs a dual approach combining unit tests for specific scenarios and property-based tests for comprehensive input coverage. This ensures both concrete edge cases and general correctness properties are validated.

### Property-Based Testing

**Framework:** Hypothesis (Python property-based testing library)

**Configuration:**
- Minimum 100 iterations per property test
- Each test tagged with comment referencing design property
- Tag format: `# Feature: inspireher-women-tech-hub, Property {number}: {property_text}`

**Property Test Coverage:**

1. **Gallery Display Property (Property 1)**
   - Generate: Random list of WomenProfile objects (0-50 profiles)
   - Action: Query gallery endpoint
   - Verify: Response contains all profile names
   - Tag: `# Feature: inspireher-women-tech-hub, Property 1: Gallery displays all profiles`

2. **Card Completeness Property (Property 2)**
   - Generate: Random WomenProfile with all fields populated
   - Action: Render profile card
   - Verify: HTML contains name, field, achievement, and image_url
   - Tag: `# Feature: inspireher-women-tech-hub, Property 2: Profile cards contain all required information`

3. **Inspiration Wall Property (Property 3)**
   - Generate: Random list of Quote objects (0-50 quotes)
   - Action: Query inspiration wall endpoint
   - Verify: Response contains all quote texts
   - Tag: `# Feature: inspireher-women-tech-hub, Property 3: Inspiration wall displays all quotes`

4. **Profile Creation Property (Property 4)**
   - Generate: Random valid profile data (non-empty strings)
   - Action: Submit profile via POST
   - Verify: Database contains new record with matching data
   - Tag: `# Feature: inspireher-women-tech-hub, Property 4: Valid profile submission creates database record`

5. **Image Upload Property (Property 5)**
   - Generate: Random image file and profile data
   - Action: Submit with image upload
   - Verify: Database record contains S3 URL (not binary), URL is accessible
   - Tag: `# Feature: inspireher-women-tech-hub, Property 5: Image upload stores S3 URL in database`

6. **Unique Filename Property (Property 6)**
   - Generate: Multiple random image files
   - Action: Upload all images
   - Verify: All generated filenames are unique
   - Tag: `# Feature: inspireher-women-tech-hub, Property 6: Unique filename generation`

7. **Validation Rejection Property (Property 7)**
   - Generate: Profile data with randomly missing required fields
   - Action: Submit invalid profile
   - Verify: No database record created, error message returned
   - Tag: `# Feature: inspireher-women-tech-hub, Property 7: Invalid submissions rejected`

8. **Redirect Property (Property 8)**
   - Generate: Random valid profile data
   - Action: Submit profile
   - Verify: Response is redirect to gallery endpoint
   - Tag: `# Feature: inspireher-women-tech-hub, Property 8: Successful submission redirects to gallery`

### Unit Testing

Unit tests complement property tests by covering specific examples, edge cases, and integration points.

**Test Categories:**

1. **Route Tests**
   - Home page returns 200 status
   - Gallery page returns 200 status
   - Inspiration wall returns 200 status
   - Submit form page returns 200 status
   - Non-existent routes return 404

2. **Empty State Tests**
   - Gallery with no profiles shows empty state message
   - Inspiration wall with no quotes shows empty state message

3. **Form Validation Tests**
   - Empty name field rejected
   - Empty field field rejected
   - Empty achievement field rejected
   - All fields empty rejected

4. **S3 Integration Tests (Mocked)**
   - Successful upload returns URL
   - S3 connection failure handled gracefully
   - Invalid credentials handled gracefully
   - Bucket not found handled gracefully

5. **Database Tests**
   - Schema initialization creates tables
   - Profile creation persists data
   - Quote creation persists data
   - Query returns all records

6. **File Upload Tests**
   - Valid image types accepted (jpg, png, gif)
   - Invalid file types rejected
   - File size limit enforced
   - Filename sanitization applied

### Test Environment Setup

**Database:**
- Use in-memory SQLite for tests (`:memory:`)
- Fresh database for each test
- Fixtures for common test data

**S3 Mocking:**
- Use `moto` library to mock boto3 S3 calls
- Simulate success and failure scenarios
- Verify upload calls without actual S3 interaction

**Flask Test Client:**
- Use Flask's built-in test client
- Configure app in testing mode
- Disable CSRF for test requests

### Testing Tools

- **pytest**: Test runner and framework
- **Hypothesis**: Property-based testing
- **moto**: AWS service mocking
- **pytest-flask**: Flask testing utilities
- **coverage.py**: Code coverage measurement

### Coverage Goals

- Minimum 80% code coverage
- 100% coverage of route handlers
- 100% coverage of error handling paths
- All correctness properties implemented as tests

### Continuous Integration

Tests should run automatically on:
- Every commit to version control
- Pull request creation
- Before deployment

### Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only property tests
pytest -k "property"

# Run only unit tests
pytest -k "unit"
```
