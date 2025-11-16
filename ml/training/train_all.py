"""Train all models."""
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
    """Train all stat models."""
    logger.info("Starting training for all models")
    
    stat_types = ["points", "assists", "rebounds"]
    
    db = SessionLocal()
    registry = ModelRegistry(settings.MODEL_DIR)
    
    try:
        for stat_type in stat_types:
            logger.info(f"\n{'='*50}")
            logger.info(f"Training {stat_type} model")
            logger.info(f"{'='*50}\n")
            
            try:
                trainer = StatModelTrainer(stat_type, db)
                X, y = trainer.load_training_data(lookback_days=120)
                trainer.train(X, y)
                trainer.save_model(registry)
                
                logger.info(f"✓ {stat_type} model training complete\n")
            except Exception as e:
                logger.error(f"✗ Failed to train {stat_type} model: {e}\n")
                continue
        
        logger.info("All model training complete")
    finally:
        db.close()


if __name__ == "__main__":
    main()
