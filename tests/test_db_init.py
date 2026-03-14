"""
Unit tests for database initialization function.
"""
import pytest
from flask import Flask
from models import db, init_db, WomenProfile, Quote


def test_init_db_creates_tables():
    """Test that init_db successfully creates database tables."""
    # Create a test Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Initialize the database
    init_db(app)
    
    # Verify tables were created by attempting to query them
    with app.app_context():
        # These queries should not raise exceptions if tables exist
        profiles = WomenProfile.query.all()
        quotes = Quote.query.all()
        
        assert profiles == []
        assert quotes == []


def test_init_db_handles_errors():
    """Test that init_db logs errors when database initialization fails."""
    # Create a test Flask app with a valid URI but simulate a database error
    # by using a path that will fail during table creation
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////invalid/path/that/does/not/exist/test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # init_db should raise an exception when it can't create tables
    with pytest.raises(Exception):
        init_db(app)


def test_init_db_idempotent():
    """Test that init_db can be called multiple times without errors."""
    # Create a test Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Call init_db multiple times
    init_db(app)
    init_db(app)
    
    # Verify tables still work correctly
    with app.app_context():
        profiles = WomenProfile.query.all()
        assert profiles == []
