"""Players service for querying player data."""
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.db.models import Player, Team
from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class PlayersService:
    """Service for managing and querying players."""
    
    def __init__(self, db: Session):
        """
        Initialize players service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def search_players(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search for players by name.
        
        Args:
            query: Search string
            limit: Maximum number of results
            
        Returns:
            List of player dictionaries
        """
        search_pattern = f"%{query}%"
        
        results = (
            self.db.query(Player, Team)
            .outerjoin(Team, Player.team_id == Team.id)
            .filter(
                or_(
                    Player.name.ilike(search_pattern),
                    Player.external_id.ilike(search_pattern),
                )
            )
            .filter(Player.is_active == True)
            .limit(limit)
            .all()
        )
        
        formatted = []
        for player, team in results:
            formatted.append({
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "team_id": team.id if team else None,
                "team_name": team.name if team else None,
                "team_abbrev": team.abbrev if team else None,
                "external_id": player.external_id,
            })
        
        return formatted
    
    def get_player_by_id(self, player_id: int) -> Optional[dict]:
        """
        Get player by ID.
        
        Args:
            player_id: Player ID
            
        Returns:
            Player dictionary or None
        """
        result = (
            self.db.query(Player, Team)
            .outerjoin(Team, Player.team_id == Team.id)
            .filter(Player.id == player_id)
            .first()
        )
        
        if not result:
            return None
        
        player, team = result
        
        return {
            "id": player.id,
            "name": player.name,
            "position": player.position,
            "team_id": team.id if team else None,
            "team_name": team.name if team else None,
            "team_abbrev": team.abbrev if team else None,
            "external_id": player.external_id,
            "is_active": player.is_active,
        }
    
    def get_all_active_players(self, limit: int = 500) -> list[dict]:
        """
        Get all active players.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of player dictionaries
        """
        results = (
            self.db.query(Player, Team)
            .outerjoin(Team, Player.team_id == Team.id)
            .filter(Player.is_active == True)
            .order_by(Player.name)
            .limit(limit)
            .all()
        )
        
        formatted = []
        for player, team in results:
            formatted.append({
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "team_id": team.id if team else None,
                "team_abbrev": team.abbrev if team else None,
            })
        
        return formatted
