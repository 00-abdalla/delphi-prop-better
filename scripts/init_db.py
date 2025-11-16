"""Initialize database - create all tables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.db import Base, engine
from backend.app.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Create all database tables."""
    logger.info("Creating database tables...")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    main()
