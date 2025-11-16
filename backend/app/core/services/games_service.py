"""Games service for querying game data."""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.db.models import Game, Team
from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class GamesService:
    """Service for managing and querying games."""
    
    def __init__(self, db: Session):
        """
        Initialize games service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_games_by_date(self, target_date: date) -> list[dict]:
        """
        Get all games for a specific date.
        
        Args:
            target_date: Date to query
            
        Returns:
            List of game dictionaries
        """
        results = (
            self.db.query(Game, Team.label("home"), Team.label("away"))
            .join(Team, Game.home_team_id == Team.id, isouter=False)
            .join(Team, Game.away_team_id == Team.id, isouter=False)
            .filter(Game.game_date == target_date)
            .all()
        )
        
        # Manual join approach
        results = (
            self.db.query(Game)
            .filter(Game.game_date == target_date)
            .all()
        )
        
        formatted = []
        for game in results:
            home_team = self.db.query(Team).filter(Team.id == game.home_team_id).first()
            away_team = self.db.query(Team).filter(Team.id == game.away_team_id).first()
            
            formatted.append({
                "id": game.id,
                "external_id": game.external_id,
                "game_date": game.game_date.isoformat(),
                "season": game.season,
                "home_team_id": game.home_team_id,
                "home_team_name": home_team.name if home_team else None,
                "home_team_abbrev": home_team.abbrev if home_team else None,
                "away_team_id": game.away_team_id,
                "away_team_name": away_team.name if away_team else None,
                "away_team_abbrev": away_team.abbrev if away_team else None,
                "home_score": game.home_score,
                "away_score": game.away_score,
                "status": game.status,
                "spread": game.spread,
                "total": game.total,
            })
        
        return formatted
    
    def get_game_by_id(self, game_id: int) -> Optional[dict]:
        """
        Get game by ID.
        
        Args:
            game_id: Game ID
            
        Returns:
            Game dictionary or None
        """
        game = self.db.query(Game).filter(Game.id == game_id).first()
        
        if not game:
            return None
        
        home_team = self.db.query(Team).filter(Team.id == game.home_team_id).first()
        away_team = self.db.query(Team).filter(Team.id == game.away_team_id).first()
        
        return {
            "id": game.id,
            "external_id": game.external_id,
            "game_date": game.game_date.isoformat(),
            "season": game.season,
            "home_team_id": game.home_team_id,
            "home_team_name": home_team.name if home_team else None,
            "home_team_abbrev": home_team.abbrev if home_team else None,
            "away_team_id": game.away_team_id,
            "away_team_name": away_team.name if away_team else None,
            "away_team_abbrev": away_team.abbrev if away_team else None,
            "home_score": game.home_score,
            "away_score": game.away_score,
            "status": game.status,
            "spread": game.spread,
            "total": game.total,
        }
    
    def get_upcoming_games(self, limit: int = 50) -> list[dict]:
        """
        Get upcoming games (today and future).
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of game dictionaries
        """
        today = date.today()
        
        results = (
            self.db.query(Game)
            .filter(Game.game_date >= today)
            .order_by(Game.game_date)
            .limit(limit)
            .all()
        )
        
        formatted = []
        for game in results:
            home_team = self.db.query(Team).filter(Team.id == game.home_team_id).first()
            away_team = self.db.query(Team).filter(Team.id == game.away_team_id).first()
            
            formatted.append({
                "id": game.id,
                "game_date": game.game_date.isoformat(),
                "home_team_abbrev": home_team.abbrev if home_team else None,
                "away_team_abbrev": away_team.abbrev if away_team else None,
                "status": game.status,
            })
        
        return formatted
