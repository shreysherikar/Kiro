import logging
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WomenProfile(db.Model):
    __tablename__ = 'women_profiles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    field = db.Column(db.String(100), nullable=False)
    achievement = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<WomenProfile {self.name}>'


class Quote(db.Model):
    __tablename__ = 'quotes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<Quote {self.id}>'


def init_db(app):
    """
    Initialize the database schema.
    
    Creates all tables defined in the models if they don't exist.
    Handles database initialization errors with logging.
    
    Args:
        app: Flask application instance
        
    Raises:
        Exception: If database initialization fails
    """
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
