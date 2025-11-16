"""Prop scoring service - generates predictions for props."""
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import settings
from backend.app.core.utils.distributions import NormalStatDistribution
from backend.app.core.utils.ev_calculations import compute_ev_and_edge
from backend.app.db.models import (
    Game,
    OddsSnapshot,
    PlayerGameFeatures,
    Prop,
    PropPrediction,
    StatType,
)
from backend.app.logging_config import get_logger
from ml.inference.model_registry import ModelRegistry

logger = get_logger(__name__)


class PropScorer:
    """Service for scoring props using trained models."""
    
    def __init__(self, db: Session, model_registry: ModelRegistry):
        """
        Initialize prop scorer.
        
        Args:
            db: Database session
            model_registry: Model registry for loading models
        """
        self.db = db
        self.registry = model_registry
        self.run_id = str(uuid.uuid4())[:8]
    
    def score_props_for_date(self, target_date: date) -> None:
        """
        Score all props for a specific date.
        
        Args:
            target_date: Date to score props for
        """
        logger.info(f"Scoring props for {target_date} (run_id: {self.run_id})")
        
        # Get all active props for the date
        props = (
            self.db.query(Prop)
            .filter(Prop.prop_date == target_date)
            .filter(Prop.is_active == True)
            .all()
        )
        
        if not props:
            logger.warning(f"No props found for {target_date}")
            return
        
        logger.info(f"Found {len(props)} props to score")
        
        scored_count = 0
        for prop in props:
            try:
                self._score_prop(prop)
                scored_count += 1
            except Exception as e:
                logger.error(f"Error scoring prop {prop.id}: {e}")
                continue
        
        self.db.commit()
        logger.info(f"Scored {scored_count}/{len(props)} props successfully")
    
    def _score_prop(self, prop: Prop) -> None:
        """
        Score a single prop.
        
        Args:
            prop: Prop object to score
        """
        # Get stat type
        stat_type = self.db.query(StatType).filter(StatType.id == prop.stat_type_id).first()
        if not stat_type:
            logger.warning(f"Stat type not found for prop {prop.id}")
            return
        
        # Load model
        model = self.registry.get_model(stat_type.name)
        if model is None:
            logger.warning(f"Model not found for stat type: {stat_type.name}")
            return
        
        # Load features
        features = (
            self.db.query(PlayerGameFeatures)
            .filter(
                and_(
                    PlayerGameFeatures.player_id == prop.player_id,
                    PlayerGameFeatures.game_id == prop.game_id,
                    PlayerGameFeatures.stat_type_id == prop.stat_type_id,
                )
            )
            .first()
        )
        
        if not features:
            logger.warning(f"Features not found for prop {prop.id}")
            return
        
        # Convert features to DataFrame
        feature_dict = features.feature_vector
        X = pd.DataFrame([feature_dict])
        
        # Predict
        predicted_mean = float(model.predict(X)[0])
        
        # Estimate variance (simple heuristic: 20% of mean or use training residuals)
        # TODO: Use actual residual variance from training
        predicted_variance = (predicted_mean * 0.3) ** 2  # Simple heuristic
        
        # Create distribution
        dist = NormalStatDistribution(mean=predicted_mean, variance=predicted_variance)
        
        # Get latest odds
        latest_odds = (
            self.db.query(OddsSnapshot)
            .filter(OddsSnapshot.prop_id == prop.id)
            .order_by(OddsSnapshot.timestamp.desc())
            .first()
        )
        
        if not latest_odds:
            logger.warning(f"No odds found for prop {prop.id}")
            return
        
        # Compute probabilities
        prob_over = dist.prob_over(prop.line)
        prob_under = dist.prob_under(prop.line)
        
        # Compute EV and edge
        ev_over, edge_over = compute_ev_and_edge(prob_over, latest_odds.over_odds)
        ev_under, edge_under = compute_ev_and_edge(prob_under, latest_odds.under_odds)
        
        # Create prediction record
        prediction = PropPrediction(
            prop_id=prop.id,
            model_name=f"lgb_{stat_type.name}_v1",
            run_id=self.run_id,
            predicted_mean=predicted_mean,
            predicted_variance=predicted_variance,
            prob_over=prob_over,
            prob_under=prob_under,
            edge_over=edge_over,
            edge_under=edge_under,
            ev_over=ev_over,
            ev_under=ev_under,
        )
        
        self.db.add(prediction)
