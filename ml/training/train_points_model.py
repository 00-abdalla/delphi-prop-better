"""Train points prediction model."""
import sys
from datetime import date, timedelta
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sqlalchemy import and_

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import settings
from backend.app.db import SessionLocal
from backend.app.db.models import BoxScore, Game, Player, PlayerGameFeatures, StatType
from backend.app.logging_config import get_logger
from ml.inference.model_registry import ModelRegistry

logger = get_logger(__name__)


class StatModelTrainer:
    """Trainer for stat prediction models."""
    
    def __init__(self, stat_type: str, db_session):
        """
        Initialize trainer.
        
        Args:
            stat_type: Stat type to train (points, assists, rebounds)
            db_session: Database session
        """
        self.stat_type = stat_type
        self.db = db_session
        self.model = None
        self.feature_names = None
    
    def load_training_data(self, lookback_days: int = 90) -> tuple[pd.DataFrame, pd.Series]:
        """
        Load training data from database.
        
        Args:
            lookback_days: Days of history to use
            
        Returns:
            Tuple of (features_df, target_series)
        """
        logger.info(f"Loading training data for {self.stat_type}")
        
        # Get stat type ID
        stat_type_obj = self.db.query(StatType).filter(StatType.name == self.stat_type).first()
        if not stat_type_obj:
            raise ValueError(f"Stat type not found: {self.stat_type}")
        
        # Get cutoff date
        cutoff_date = date.today() - timedelta(days=lookback_days)
        
        # Query features and actual results
        query = (
            self.db.query(PlayerGameFeatures, BoxScore, Game)
            .join(Game, PlayerGameFeatures.game_id == Game.id)
            .join(
                BoxScore,
                and_(
                    BoxScore.player_id == PlayerGameFeatures.player_id,
                    BoxScore.game_id == PlayerGameFeatures.game_id,
                ),
            )
            .filter(PlayerGameFeatures.stat_type_id == stat_type_obj.id)
            .filter(Game.game_date >= cutoff_date)
            .filter(Game.status == "final")
        )
        
        results = query.all()
        
        if not results:
            raise ValueError(f"No training data found for {self.stat_type}")
        
        logger.info(f"Found {len(results)} training samples")
        
        # Build DataFrame
        records = []
        for features, box_score, game in results:
            feature_dict = features.feature_vector.copy()
            
            # Add target
            if self.stat_type == "points":
                target = box_score.points or 0
            elif self.stat_type == "assists":
                target = box_score.assists or 0
            elif self.stat_type == "rebounds":
                target = box_score.rebounds or 0
            else:
                target = 0
            
            feature_dict["target"] = target
            records.append(feature_dict)
        
        df = pd.DataFrame(records)
        
        # Separate features and target
        X = df.drop(columns=["target"])
        y = df["target"]
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        logger.info(f"Features: {self.feature_names}")
        logger.info(f"Target stats - mean: {y.mean():.2f}, std: {y.std():.2f}")
        
        return X, y
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Train the model.
        
        Args:
            X: Features DataFrame
            y: Target Series
        """
        logger.info(f"Training {self.stat_type} model")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        # Parameters
        params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
        }
        
        # Train
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[train_data, val_data],
            valid_names=["train", "val"],
        )
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_val = self.model.predict(X_val)
        
        train_rmse = np.sqrt(np.mean((y_train - y_pred_train) ** 2))
        val_rmse = np.sqrt(np.mean((y_val - y_pred_val) ** 2))
        
        logger.info(f"Train RMSE: {train_rmse:.3f}")
        logger.info(f"Val RMSE: {val_rmse:.3f}")
    
    def save_model(self, registry: ModelRegistry) -> None:
        """
        Save the trained model.
        
        Args:
            registry: Model registry instance
        """
        if self.model is None:
            raise ValueError("No model to save. Train first.")
        
        registry.save_model(self.model, self.stat_type)
        logger.info(f"Model saved for {self.stat_type}")


def main():
    """Train points model."""
    logger.info("Starting points model training")
    
    db = SessionLocal()
    
    try:
        trainer = StatModelTrainer("points", db)
        X, y = trainer.load_training_data(lookback_days=120)
        trainer.train(X, y)
        
        registry = ModelRegistry(settings.MODEL_DIR)
        trainer.save_model(registry)
        
        logger.info("Points model training complete")
    finally:
        db.close()


if __name__ == "__main__":
    main()
