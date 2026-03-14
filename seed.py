"""
Seed data for InspireHer Women in Tech Inspiration Hub.

Provides initial motivational quotes about women in technology.
The seed function checks for existing quotes before inserting to avoid duplicates.
"""

import logging

logger = logging.getLogger(__name__)

INITIAL_QUOTES = [
    "The most courageous act is still to think for yourself. Aloud. — Coco Chanel",
    "Science and everyday life cannot and should not be separated. — Rosalind Franklin",
    "I was taught that the way of progress was neither swift nor easy. — Marie Curie",
    "The question isn't who's going to let me; it's who is going to stop me. — Ayn Rand",
    "If you're offered a seat on a rocket ship, don't ask what seat! Just get on. — Sheryl Sandberg",
    "We need to accept that we won't always make the right decisions, that we'll screw up royally sometimes — understanding that failure is not the opposite of success, it's part of success. — Arianna Huffington",
    "One of the most courageous things you can do is identify yourself, know who you are, what you believe in and where you want to go. — Sheila Murray Bethel",
    "The most effective way to do it, is to do it. — Amelia Earhart",
]


def seed_quotes(app):
    """
    Seed the database with initial motivational quotes.

    Checks if any quotes already exist before inserting to avoid duplicates.
    Safe to call on every app startup.

    Args:
        app: Flask application instance
    """
    from models import db, Quote

    with app.app_context():
        existing_count = Quote.query.count()
        if existing_count > 0:
            logger.info(f"Quotes already seeded ({existing_count} found). Skipping.")
            return

        try:
            for text in INITIAL_QUOTES:
                db.session.add(Quote(text=text))
            db.session.commit()
            logger.info(f"Seeded {len(INITIAL_QUOTES)} motivational quotes.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to seed quotes: {str(e)}")
            raise
