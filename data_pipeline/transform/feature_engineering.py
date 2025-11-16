"""Feature engineering service."""
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.app.db.models import BoxScore, Game, Player, PlayerGameFeatures, StatType
from backend.app.logging_config import get_logger
from data_pipeline.transform.minutes_projection import MinutesProjector

logger = get_logger(__name__)


class FeatureEngineer:
    """Service for building player game features."""
    
    def __init__(self, db: Session):
        """
        Initialize feature engineer.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.minutes_projector = MinutesProjector()
    
    def build_player_game_features_for_date(self, target_date: date) -> None:
        """
        Build features for all players in games on target date.
        
        Args:
            target_date: Date to build features for
        """
        logger.info(f"Building features for {target_date}")
        
        # Get games for target date
        games = self.db.query(Game).filter(Game.game_date == target_date).all()
        
        if not games:
            logger.warning(f"No games found for {target_date}")
            return
        
        # Get stat types
        stat_types = self.db.query(StatType).all()
        stat_type_map = {st.name: st.id for st in stat_types}
        
        for game in games:
            logger.info(f"Processing game {game.id}: {game.external_id}")
            
            # Get players from both teams
            home_players = self.db.query(Player).filter(Player.team_id == game.home_team_id).all()
            away_players = self.db.query(Player).filter(Player.team_id == game.away_team_id).all()
            
            all_players = home_players + away_players
            
            for player in all_players:
                for stat_name in ["points", "assists", "rebounds"]:
                    stat_type_id = stat_type_map.get(stat_name)
                    if not stat_type_id:
                        continue
                    
                    features = self._build_features_for_player_stat(
                        player=player,
                        game=game,
                        stat_name=stat_name,
                        target_date=target_date,
                    )
                    
                    if features:
                        # Upsert features
                        existing = (
                            self.db.query(PlayerGameFeatures)
                            .filter(
                                and_(
                                    PlayerGameFeatures.player_id == player.id,
                                    PlayerGameFeatures.game_id == game.id,
                                    PlayerGameFeatures.stat_type_id == stat_type_id,
                                )
                            )
                            .first()
                        )
                        
                        if existing:
                            existing.feature_vector = features
                            existing.feature_schema_version = 1
                        else:
                            feature_obj = PlayerGameFeatures(
                                player_id=player.id,
                                game_id=game.id,
                                stat_type_id=stat_type_id,
                                feature_schema_version=1,
                                feature_vector=features,
                            )
                            self.db.add(feature_obj)
        
        self.db.commit()
        logger.info(f"Finished building features for {target_date}")
    
    def _build_features_for_player_stat(
        self,
        player: Player,
        game: Game,
        stat_name: str,
        target_date: date,
    ) -> dict:
        """
        Build feature vector for a player/game/stat combination.
        
        Args:
            player: Player object
            game: Game object
            stat_name: Stat name (points, assists, rebounds)
            target_date: Target game date
            
        Returns:
            Feature dictionary
        """
        # Get historical box scores before target date
        historical_box_scores = (
            self.db.query(BoxScore, Game)
            .join(Game, BoxScore.game_id == Game.id)
            .filter(BoxScore.player_id == player.id)
            .filter(Game.game_date < target_date)
            .order_by(Game.game_date.desc())
            .limit(20)  # Last 20 games
            .all()
        )
        
        if not historical_box_scores:
            return {}
        
        # Convert to DataFrame
        records = []
        for box_score, hist_game in historical_box_scores:
            records.append({
                "game_date": hist_game.game_date,
                "minutes": box_score.minutes or 0,
                "points": box_score.points or 0,
                "assists": box_score.assists or 0,
                "rebounds": box_score.rebounds or 0,
            })
        
        df = pd.DataFrame(records).sort_values("game_date", ascending=False)
        
        # Compute rolling averages
        stat_col = stat_name
        features = {
            f"{stat_name}_mean_3": df[stat_col].head(3).mean() if len(df) >= 3 else df[stat_col].mean(),
            f"{stat_name}_mean_5": df[stat_col].head(5).mean() if len(df) >= 5 else df[stat_col].mean(),
            f"{stat_name}_mean_10": df[stat_col].head(10).mean() if len(df) >= 10 else df[stat_col].mean(),
            f"{stat_name}_std_10": df[stat_col].head(10).std() if len(df) >= 10 else df[stat_col].std(),
            "minutes_mean_5": df["minutes"].head(5).mean() if len(df) >= 5 else df["minutes"].mean(),
            "minutes_projected": self.minutes_projector.project(df),
            "games_played_last_10": min(len(df), 10),
            "games_played_last_20": len(df),
        }
        
        # Game context
        features.update({
            "spread": game.spread or 0.0,
            "total": game.total or 220.0,
            "is_home": 1 if player.team_id == game.home_team_id else 0,
        })
        
        # Fill NaNs
        for key, value in features.items():
            if pd.isna(value):
                features[key] = 0.0
        
        return features
