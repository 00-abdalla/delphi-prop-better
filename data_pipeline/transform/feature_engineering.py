"""Feature engineering service."""
from datetime import date, timedelta
from typing import Dict, List, Tuple

import pandas as pd
from sqlalchemy import and_, delete
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
        OPTIMIZED: Uses batch queries and bulk inserts.
        
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
        
        # Collect all unique player IDs from games
        game_ids = [g.id for g in games]
        all_player_ids = set()
        game_player_map = {}  # game_id -> list of player_ids
        
        for game in games:
            home_players = self.db.query(Player.id).filter(Player.team_id == game.home_team_id).all()
            away_players = self.db.query(Player.id).filter(Player.team_id == game.away_team_id).all()
            
            player_ids = [p.id for p in home_players] + [p.id for p in away_players]
            game_player_map[game.id] = player_ids
            all_player_ids.update(player_ids)
        
        # Batch load all historical box scores for all players (before target_date)
        logger.info(f"Loading historical data for {len(all_player_ids)} players")
        historical_data = (
            self.db.query(BoxScore, Game, BoxScore.player_id)
            .join(Game, BoxScore.game_id == Game.id)
            .filter(BoxScore.player_id.in_(all_player_ids))
            .filter(Game.game_date < target_date)
            .order_by(BoxScore.player_id, Game.game_date.desc())
            .all()
        )
        
        # Organize by player_id
        player_history: Dict[int, List[Tuple[BoxScore, Game]]] = {}
        for box_score, game, player_id in historical_data:
            if player_id not in player_history:
                player_history[player_id] = []
            player_history[player_id].append((box_score, game))
        
        # Load players in batch
        players = self.db.query(Player).filter(Player.id.in_(all_player_ids)).all()
        player_map = {p.id: p for p in players}
        
        # Load games in batch (already have them, create map)
        game_map = {g.id: g for g in games}
        
        # Delete existing features for this date to avoid duplicates
        logger.info(f"Clearing existing features for {target_date}")
        self.db.execute(
            delete(PlayerGameFeatures).where(
                PlayerGameFeatures.game_id.in_(game_ids)
            )
        )
        
        # Build all features in memory
        logger.info(f"Computing features for {len(games)} games")
        features_to_insert = []
        
        for game in games:
            player_ids = game_player_map.get(game.id, [])
    def _build_features_from_history(
        self,
        history: List[Tuple[BoxScore, Game]],
        player: Player,
        game: Game,
        stat_name: str,
    ) -> dict:
        """
        Build feature vector from pre-loaded history.
        OPTIMIZED: No DB queries, just computation.
        
        Args:
            history: List of (BoxScore, Game) tuples (already sorted desc by date)
            player: Player object
            game: Game object for context
            stat_name: Stat name (points, assists, rebounds)
            
        Returns:
            Feature dictionary
        """
        if not history:
            return {}
        
        # Convert to DataFrame
        records = []
        for box_score, hist_game in history:
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
    
    def _build_features_for_player_stat(
        self,
        player: Player,
        game: Game,
        stat_name: str,
        target_date: date,
    ) -> dict:
        """
        Build feature vector for a player/game/stat combination.
        LEGACY METHOD: Kept for backward compatibility, but slow.
        Use build_player_game_features_for_date for batch processing.
        
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
        
        return self._build_features_from_history(
            history=historical_box_scores,
            player=player,
            game=game,
            stat_name=stat_name,
        )
