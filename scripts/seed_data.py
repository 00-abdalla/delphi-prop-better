"""Seed initial data into the database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.db import SessionLocal, StatType
from backend.app.logging_config import get_logger

logger = get_logger(__name__)


def seed_stat_types(db: SessionLocal) -> None:
    """Seed stat_types table with canonical stat types."""
    stat_types_data = [
        {
            "name": "points",
            "display_name": "Points",
            "abbreviation": "PTS",
        },
        {
            "name": "assists",
            "display_name": "Assists",
            "abbreviation": "AST",
        },
        {
            "name": "rebounds",
            "display_name": "Rebounds",
            "abbreviation": "REB",
        },
        {
            "name": "steals",
            "display_name": "Steals",
            "abbreviation": "STL",
        },
        {
            "name": "blocks",
            "display_name": "Blocks",
            "abbreviation": "BLK",
        },
        {
            "name": "threes",
            "display_name": "Three Pointers Made",
            "abbreviation": "3PM",
        },
        {
            "name": "points_rebounds_assists",
            "display_name": "Points + Rebounds + Assists",
            "abbreviation": "PRA",
        },
        {
            "name": "points_rebounds",
            "display_name": "Points + Rebounds",
            "abbreviation": "PR",
        },
        {
            "name": "points_assists",
            "display_name": "Points + Assists",
            "abbreviation": "PA",
        },
        {
            "name": "rebounds_assists",
            "display_name": "Rebounds + Assists",
            "abbreviation": "RA",
        },
    ]
    
    count = 0
    for st_data in stat_types_data:
        existing = db.query(StatType).filter(StatType.name == st_data["name"]).first()
        if not existing:
            stat_type = StatType(**st_data)
            db.add(stat_type)
            count += 1
            logger.info(f"Created stat_type: {st_data['name']}")
        else:
            logger.info(f"Stat_type already exists: {st_data['name']}")
    
    db.commit()
    logger.info(f"✓ Seeded {count} new stat types (total: {len(stat_types_data)})")


def main() -> None:
    """Run all seed functions."""
    logger.info("Starting database seeding...")
    
    db = SessionLocal()
    try:
        seed_stat_types(db)
        logger.info("✓ Database seeding complete!")
    except Exception as e:
        logger.error(f"✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
