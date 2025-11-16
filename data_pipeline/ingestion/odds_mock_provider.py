"""Mock odds/sportsbook data provider."""
import random
from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class BaseOddsProvider(ABC):
    """Abstract base class for odds data providers."""
    
    @abstractmethod
    def get_props_for_games(self, games: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get props for a list of games."""
        pass


class OddsMockProvider(BaseOddsProvider):
    """Mock provider that generates fake odds and props."""
    
    def __init__(self):
        """Initialize mock odds provider."""
        self.sportsbooks = ["fanduel", "draftkings", "bet365", "caesars"]
        self.stat_types = ["points", "assists", "rebounds"]
    
    def get_props_for_games(self, games: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Generate fake props for games.
        
        Args:
            games: List of game dictionaries with player info
            
        Returns:
            List of prop dictionaries
        """
        props = []
        
        for game in games:
            game_date = game.get("game_date")
            if isinstance(game_date, str):
                game_date = date.fromisoformat(game_date)
            
            players = game.get("players", [])
            
            # Generate 3-5 props per player per stat type
            for player in players[:10]:  # Top 10 players per game
                for stat_type in self.stat_types:
                    # Not every player gets every stat type
                    if random.random() < 0.7:  # 70% chance
                        sportsbook = random.choice(self.sportsbooks)
                        
                        # Generate realistic lines based on stat type
                        if stat_type == "points":
                            line = round(random.uniform(15.5, 32.5), 1)
                        elif stat_type == "assists":
                            line = round(random.uniform(3.5, 10.5), 1)
                        elif stat_type == "rebounds":
                            line = round(random.uniform(5.5, 13.5), 1)
                        else:
                            line = round(random.uniform(10.5, 25.5), 1)
                        
                        # Generate American odds (typically -110 to -120 for both sides)
                        over_odds = random.choice([-120, -115, -110, -108, -105])
                        under_odds = random.choice([-120, -115, -110, -108, -105])
                        
                        props.append({
                            "game_external_id": game["external_id"],
                            "player_external_id": player["external_id"],
                            "stat_type": stat_type,
                            "sportsbook": sportsbook,
                            "line": line,
                            "over_odds": over_odds,
                            "under_odds": under_odds,
                            "prop_date": game_date,
                        })
        
        logger.info(f"Mock odds provider: generated {len(props)} props")
        return props
    
    def get_line_movement(self, existing_props: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Simulate line movement for existing props.
        
        Args:
            existing_props: Existing props to update
            
        Returns:
            Updated props with new odds
        """
        updated_props = []
        
        for prop in existing_props:
            # 30% chance of line movement
            if random.random() < 0.3:
                # Move line by 0.5 or 1.0
                line_change = random.choice([-1.0, -0.5, 0.5, 1.0])
                new_line = prop["line"] + line_change
                
                # Adjust odds
                over_odds = random.choice([-125, -120, -115, -110, -105, -102, +100, +105])
                under_odds = random.choice([-125, -120, -115, -110, -105, -102, +100, +105])
            else:
                # Just odds movement
                new_line = prop["line"]
                odds_change = random.choice([-5, -3, 0, 3, 5])
                over_odds = prop["over_odds"] + odds_change
                under_odds = prop["under_odds"] - odds_change
            
            updated_props.append({
                **prop,
                "line": new_line,
                "over_odds": over_odds,
                "under_odds": under_odds,
            })
        
        return updated_props
