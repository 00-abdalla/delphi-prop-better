"""Train rebounds prediction model - same structure as points."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import settings
from backend.app.db import SessionLocal
from backend.app.logging_config import get_logger
from ml.inference.model_registry import ModelRegistry
from ml.training.train_points_model import StatModelTrainer

logger = get_logger(__name__)


def main():
    """Train rebounds model."""
    logger.info("Starting rebounds model training")
    
    db = SessionLocal()
    
    try:
        trainer = StatModelTrainer("rebounds", db)
        X, y = trainer.load_training_data(lookback_days=120)
        trainer.train(X, y)
        
        registry = ModelRegistry(settings.MODEL_DIR)
        trainer.save_model(registry)
        
        logger.info("Rebounds model training complete")
    finally:
        db.close()


if __name__ == "__main__":
    main()
