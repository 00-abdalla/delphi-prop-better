"""Model registry for loading trained models."""
from pathlib import Path
from typing import Optional

import lightgbm as lgb

from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class ModelRegistry:
    """Registry for managing and loading trained models."""
    
    def __init__(self, model_dir: str):
        """
        Initialize model registry.
        
        Args:
            model_dir: Directory containing saved model files
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, lgb.Booster] = {}
    
    def get_model(self, stat_type: str) -> Optional[lgb.Booster]:
        """
        Load and cache a model for a stat type.
        
        Args:
            stat_type: Stat type name (points, assists, rebounds)
            
        Returns:
            Loaded LightGBM model or None if not found
        """
        if stat_type in self._cache:
            return self._cache[stat_type]
        
        model_path = self.model_dir / f"{stat_type}_model.txt"
        
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}")
            return None
        
        logger.info(f"Loading model from {model_path}")
        model = lgb.Booster(model_file=str(model_path))
        self._cache[stat_type] = model
        
        return model
    
    def save_model(self, model: lgb.Booster, stat_type: str) -> None:
        """
        Save a trained model.
        
        Args:
            model: Trained LightGBM model
            stat_type: Stat type name
        """
        model_path = self.model_dir / f"{stat_type}_model.txt"
        model.save_model(str(model_path))
        logger.info(f"Saved model to {model_path}")
        
        # Update cache
        self._cache[stat_type] = model
    
    def clear_cache(self) -> None:
        """Clear the model cache."""
        self._cache.clear()
        logger.info("Cleared model cache")
