"""Props service for querying and filtering prop predictions."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, joinedload

from backend.app.db.models import (
    Game,
    OddsSnapshot,
    Player,
    Prop,
    PropPrediction,
    StatType,
    Team,
)
from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class PropsService:
    """Service for managing and querying prop predictions."""
    
    def __init__(self, db: Session):
        """
        Initialize props service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_top_props(
        self,
        stat_type: str = "points",
        min_edge: float = 0.05,
        limit: int = 50,
        target_date: Optional[date] = None,
    ) -> list[dict]:
        """
        Get top prop edges by stat type.
        
        Args:
            stat_type: Canonical stat type name (points, assists, rebounds)
            min_edge: Minimum edge threshold
            limit: Maximum number of results
            target_date: Date to filter props (defaults to today)
            
        Returns:
            List of prop dictionaries with all relevant data
        """
        if target_date is None:
            target_date = date.today()
        
        # Subquery for latest odds per prop
        latest_odds_subq = (
            self.db.query(
                OddsSnapshot.prop_id,
                func.max(OddsSnapshot.timestamp).label("max_timestamp"),
            )
            .group_by(OddsSnapshot.prop_id)
            .subquery()
        )
        
        # Subquery for latest prediction per prop
        latest_pred_subq = (
            self.db.query(
                PropPrediction.prop_id,
                func.max(PropPrediction.created_at).label("max_created"),
            )
            .group_by(PropPrediction.prop_id)
            .subquery()
        )
        
        # Main query
        query = (
            self.db.query(
                Prop,
                Player,
                Team,
                Game,
                StatType,
                OddsSnapshot,
                PropPrediction,
            )
            .join(Player, Prop.player_id == Player.id)
            .join(Team, Player.team_id == Team.id)
            .join(Game, Prop.game_id == Game.id)
            .join(StatType, Prop.stat_type_id == StatType.id)
            .join(
                latest_odds_subq,
                and_(
                    Prop.id == latest_odds_subq.c.prop_id,
                ),
            )
            .join(
                OddsSnapshot,
                and_(
                    OddsSnapshot.prop_id == latest_odds_subq.c.prop_id,
                    OddsSnapshot.timestamp == latest_odds_subq.c.max_timestamp,
                ),
            )
            .join(
                latest_pred_subq,
                Prop.id == latest_pred_subq.c.prop_id,
            )
            .join(
                PropPrediction,
                and_(
                    PropPrediction.prop_id == latest_pred_subq.c.prop_id,
                    PropPrediction.created_at == latest_pred_subq.c.max_created,
                ),
            )
            .filter(StatType.name == stat_type)
            .filter(Prop.prop_date == target_date)
            .filter(Prop.is_active == True)
        )
        
        # Filter by edge (best of over/under)
        results = query.all()
        
        formatted_results = []
        for prop, player, team, game, stat_type_obj, odds, prediction in results:
            # Determine best side based on edge
            if prediction.edge_over >= prediction.edge_under:
                best_side = "over"
                best_edge = prediction.edge_over
                best_ev = prediction.ev_over
                best_odds = odds.over_odds
                best_prob = prediction.prob_over
            else:
                best_side = "under"
                best_edge = prediction.edge_under
                best_ev = prediction.ev_under
                best_odds = odds.under_odds
                best_prob = prediction.prob_under
            
            # Filter by minimum edge
            if best_edge < min_edge:
                continue
            
            formatted_results.append({
                "prop_id": prop.id,
                "player_name": player.name,
                "player_id": player.id,
                "team_abbrev": team.abbrev,
                "stat_type": stat_type_obj.name,
                "stat_display": stat_type_obj.display_name,
                "line": prop.line,
                "side": best_side,
                "odds": best_odds,
                "edge": round(best_edge, 4),
                "ev": round(best_ev, 4),
                "model_prob": round(best_prob, 4),
                "predicted_mean": round(prediction.predicted_mean, 2),
                "game_id": game.id,
                "game_date": game.game_date.isoformat(),
                "opponent": (
                    game.away_team.abbrev if player.team_id == game.home_team_id else game.home_team.abbrev
                ),
                "sportsbook": prop.sportsbook,
            })
        
        # Sort by edge descending
        formatted_results.sort(key=lambda x: x["edge"], reverse=True)
        
        return formatted_results[:limit]
    
    def get_props_for_player(self, player_id: int, target_date: Optional[date] = None) -> list[dict]:
        """
        Get all props for a specific player.
        
        Args:
            player_id: Player ID
            target_date: Date to filter props (defaults to today)
            
        Returns:
            List of prop dictionaries
        """
        if target_date is None:
            target_date = date.today()
        
        # Subquery for latest odds
        latest_odds_subq = (
            self.db.query(
                OddsSnapshot.prop_id,
                func.max(OddsSnapshot.timestamp).label("max_timestamp"),
            )
            .group_by(OddsSnapshot.prop_id)
            .subquery()
        )
        
        # Subquery for latest prediction
        latest_pred_subq = (
            self.db.query(
                PropPrediction.prop_id,
                func.max(PropPrediction.created_at).label("max_created"),
            )
            .group_by(PropPrediction.prop_id)
            .subquery()
        )
        
        query = (
            self.db.query(
                Prop,
                StatType,
                Game,
                OddsSnapshot,
                PropPrediction,
            )
            .join(StatType, Prop.stat_type_id == StatType.id)
            .join(Game, Prop.game_id == Game.id)
            .join(
                latest_odds_subq,
                Prop.id == latest_odds_subq.c.prop_id,
            )
            .join(
                OddsSnapshot,
                and_(
                    OddsSnapshot.prop_id == latest_odds_subq.c.prop_id,
                    OddsSnapshot.timestamp == latest_odds_subq.c.max_timestamp,
                ),
            )
            .outerjoin(
                latest_pred_subq,
                Prop.id == latest_pred_subq.c.prop_id,
            )
            .outerjoin(
                PropPrediction,
                and_(
                    PropPrediction.prop_id == latest_pred_subq.c.prop_id,
                    PropPrediction.created_at == latest_pred_subq.c.max_created,
                ),
            )
            .filter(Prop.player_id == player_id)
            .filter(Prop.prop_date == target_date)
            .filter(Prop.is_active == True)
        )
        
        results = query.all()
        
        formatted = []
        for prop, stat_type_obj, game, odds, prediction in results:
            prop_dict = {
                "prop_id": prop.id,
                "stat_type": stat_type_obj.name,
                "stat_display": stat_type_obj.display_name,
                "line": prop.line,
                "sportsbook": prop.sportsbook,
                "over_odds": odds.over_odds,
                "under_odds": odds.under_odds,
                "game_date": game.game_date.isoformat(),
            }
            
            if prediction:
                prop_dict.update({
                    "predicted_mean": round(prediction.predicted_mean, 2),
                    "prob_over": round(prediction.prob_over, 4),
                    "prob_under": round(prediction.prob_under, 4),
                    "edge_over": round(prediction.edge_over, 4),
                    "edge_under": round(prediction.edge_under, 4),
                    "ev_over": round(prediction.ev_over, 4),
                    "ev_under": round(prediction.ev_under, 4),
                })
            
            formatted.append(prop_dict)
        
        return formatted
    
    def get_props_for_game(self, game_id: int) -> list[dict]:
        """
        Get all props for a specific game.
        
        Args:
            game_id: Game ID
            
        Returns:
            List of prop dictionaries
        """
        # Subquery for latest odds
        latest_odds_subq = (
            self.db.query(
                OddsSnapshot.prop_id,
                func.max(OddsSnapshot.timestamp).label("max_timestamp"),
            )
            .group_by(OddsSnapshot.prop_id)
            .subquery()
        )
        
        # Subquery for latest prediction
        latest_pred_subq = (
            self.db.query(
                PropPrediction.prop_id,
                func.max(PropPrediction.created_at).label("max_created"),
            )
            .group_by(PropPrediction.prop_id)
            .subquery()
        )
        
        query = (
            self.db.query(
                Prop,
                Player,
                Team,
                StatType,
                OddsSnapshot,
                PropPrediction,
            )
            .join(Player, Prop.player_id == Player.id)
            .join(Team, Player.team_id == Team.id)
            .join(StatType, Prop.stat_type_id == StatType.id)
            .join(
                latest_odds_subq,
                Prop.id == latest_odds_subq.c.prop_id,
            )
            .join(
                OddsSnapshot,
                and_(
                    OddsSnapshot.prop_id == latest_odds_subq.c.prop_id,
                    OddsSnapshot.timestamp == latest_odds_subq.c.max_timestamp,
                ),
            )
            .outerjoin(
                latest_pred_subq,
                Prop.id == latest_pred_subq.c.prop_id,
            )
            .outerjoin(
                PropPrediction,
                and_(
                    PropPrediction.prop_id == latest_pred_subq.c.prop_id,
                    PropPrediction.created_at == latest_pred_subq.c.max_created,
                ),
            )
            .filter(Prop.game_id == game_id)
            .filter(Prop.is_active == True)
        )
        
        results = query.all()
        
        formatted = []
        for prop, player, team, stat_type_obj, odds, prediction in results:
            prop_dict = {
                "prop_id": prop.id,
                "player_name": player.name,
                "player_id": player.id,
                "team_abbrev": team.abbrev,
                "stat_type": stat_type_obj.name,
                "stat_display": stat_type_obj.display_name,
                "line": prop.line,
                "sportsbook": prop.sportsbook,
                "over_odds": odds.over_odds,
                "under_odds": odds.under_odds,
            })
            
            if prediction:
                # Determine best side
                if prediction.edge_over >= prediction.edge_under:
                    best_side = "over"
                    best_edge = prediction.edge_over
                    best_ev = prediction.ev_over
                else:
                    best_side = "under"
                    best_edge = prediction.edge_under
                    best_ev = prediction.ev_under
                
                prop_dict.update({
                    "predicted_mean": round(prediction.predicted_mean, 2),
                    "prob_over": round(prediction.prob_over, 4),
                    "prob_under": round(prediction.prob_under, 4),
                    "edge_over": round(prediction.edge_over, 4),
                    "edge_under": round(prediction.edge_under, 4),
                    "ev_over": round(prediction.ev_over, 4),
                    "ev_under": round(prediction.ev_under, 4),
                    "best_side": best_side,
                    "best_edge": round(best_edge, 4),
                    "best_ev": round(best_ev, 4),
                })
            
            formatted.append(prop_dict)
        
        # Sort by best edge descending
        formatted.sort(key=lambda x: x.get("best_edge", 0), reverse=True)
        
        return formatted
