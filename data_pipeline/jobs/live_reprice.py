"""Live reprice job - update odds and re-score props."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import settings
from backend.app.db import SessionLocal
from backend.app.db.models import OddsSnapshot, Prop
from backend.app.logging_config import get_logger
from data_pipeline.ingestion.odds_mock_provider import OddsMockProvider
from ml.inference.model_registry import ModelRegistry
from ml.inference.scorer import PropScorer

logger = get_logger(__name__)


def main():
    """Run live reprice job."""
    logger.info("Starting live reprice job")
    
    target_date = date.today()
    db = SessionLocal()
    
    try:
        odds_provider = OddsMockProvider()
        
        # Get active props for today
        props = (
            db.query(Prop)
            .filter(Prop.prop_date == target_date)
            .filter(Prop.is_active == True)
            .all()
        )
        
        if not props:
            logger.info(f"No active props for {target_date}")
            return
        
        logger.info(f"Repricing {len(props)} props")
        
        # Simulate line movement for existing props
        existing_props_data = []
        for prop in props:
            # Get latest odds
            latest_odds = (
                db.query(OddsSnapshot)
                .filter(OddsSnapshot.prop_id == prop.id)
                .order_by(OddsSnapshot.timestamp.desc())
                .first()
            )
            
            if latest_odds:
                existing_props_data.append({
                    "prop_id": prop.id,
                    "line": prop.line,
                    "over_odds": latest_odds.over_odds,
                    "under_odds": latest_odds.under_odds,
                })
        
        # Get updated odds from provider (simulates line movement)
        updated_props = odds_provider.get_line_movement(existing_props_data)
        
        # Update odds snapshots
        for updated in updated_props:
            prop_id = updated["prop_id"]
            
            # Create new odds snapshot
            odds_snapshot = OddsSnapshot(
                prop_id=prop_id,
                over_odds=updated["over_odds"],
                under_odds=updated["under_odds"],
            )
            db.add(odds_snapshot)
            
            # Update line if changed
            if updated["line"] != existing_props_data[0]["line"]:
                prop = db.query(Prop).filter(Prop.id == prop_id).first()
                if prop:
                    prop.line = updated["line"]
        
        db.commit()
        logger.info("Updated odds snapshots")
        
        # Re-score props with new odds
        logger.info("Re-scoring props")
        model_registry = ModelRegistry(settings.MODEL_DIR)
        scorer = PropScorer(db, model_registry)
        scorer.score_props_for_date(target_date)
        
        logger.info("Live reprice job complete")
    
    except Exception as e:
        logger.error(f"Error during live reprice: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
