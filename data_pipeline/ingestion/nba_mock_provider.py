"""Mock NBA data provider."""
import random
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Any

from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class BaseNBAProvider(ABC):
    """Abstract base class for NBA data providers."""
    
    @abstractmethod
    def get_teams(self) -> list[dict[str, Any]]:
        """Get all NBA teams."""
        pass
    
    @abstractmethod
    def get_players(self) -> list[dict[str, Any]]:
        """Get all NBA players."""
        pass
    
    @abstractmethod
    def get_games(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Get games in date range."""
        pass
    
    @abstractmethod
    def get_box_scores(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Get box scores for games in date range."""
        pass


class NBAMockProvider(BaseNBAProvider):
    """Mock provider that generates fake NBA data."""
    
    def __init__(self):
        """Initialize mock provider with seed data."""
        self.teams_data = self._generate_teams()
        self.players_data = self._generate_players()
    
    def _generate_teams(self) -> list[dict[str, Any]]:
        """Generate fake NBA teams."""
        teams = [
            {"external_id": "LAL", "name": "Los Angeles Lakers", "abbrev": "LAL"},
            {"external_id": "BOS", "name": "Boston Celtics", "abbrev": "BOS"},
            {"external_id": "GSW", "name": "Golden State Warriors", "abbrev": "GSW"},
            {"external_id": "MIL", "name": "Milwaukee Bucks", "abbrev": "MIL"},
            {"external_id": "PHX", "name": "Phoenix Suns", "abbrev": "PHX"},
            {"external_id": "DEN", "name": "Denver Nuggets", "abbrev": "DEN"},
            {"external_id": "DAL", "name": "Dallas Mavericks", "abbrev": "DAL"},
            {"external_id": "MIA", "name": "Miami Heat", "abbrev": "MIA"},
            {"external_id": "PHI", "name": "Philadelphia 76ers", "abbrev": "PHI"},
            {"external_id": "LAC", "name": "LA Clippers", "abbrev": "LAC"},
            {"external_id": "NYK", "name": "New York Knicks", "abbrev": "NYK"},
            {"external_id": "BKN", "name": "Brooklyn Nets", "abbrev": "BKN"},
            {"external_id": "CLE", "name": "Cleveland Cavaliers", "abbrev": "CLE"},
            {"external_id": "SAC", "name": "Sacramento Kings", "abbrev": "SAC"},
            {"external_id": "MIN", "name": "Minnesota Timberwolves", "abbrev": "MIN"},
            {"external_id": "ATL", "name": "Atlanta Hawks", "abbrev": "ATL"},
            {"external_id": "OKC", "name": "Oklahoma City Thunder", "abbrev": "OKC"},
            {"external_id": "MEM", "name": "Memphis Grizzlies", "abbrev": "MEM"},
            {"external_id": "NOP", "name": "New Orleans Pelicans", "abbrev": "NOP"},
            {"external_id": "CHI", "name": "Chicago Bulls", "abbrev": "CHI"},
            {"external_id": "TOR", "name": "Toronto Raptors", "abbrev": "TOR"},
            {"external_id": "POR", "name": "Portland Trail Blazers", "abbrev": "POR"},
            {"external_id": "UTA", "name": "Utah Jazz", "abbrev": "UTA"},
            {"external_id": "WAS", "name": "Washington Wizards", "abbrev": "WAS"},
            {"external_id": "IND", "name": "Indiana Pacers", "abbrev": "IND"},
            {"external_id": "CHA", "name": "Charlotte Hornets", "abbrev": "CHA"},
            {"external_id": "SAS", "name": "San Antonio Spurs", "abbrev": "SAS"},
            {"external_id": "DET", "name": "Detroit Pistons", "abbrev": "DET"},
            {"external_id": "ORL", "name": "Orlando Magic", "abbrev": "ORL"},
            {"external_id": "HOU", "name": "Houston Rockets", "abbrev": "HOU"},
        ]
        return teams
    
    def _generate_players(self) -> list[dict[str, Any]]:
        """Generate fake NBA players."""
        first_names = [
            "LeBron", "Stephen", "Kevin", "Giannis", "Luka", "Nikola", "Joel",
            "Jayson", "Damian", "Anthony", "James", "Kawhi", "Paul", "Devin",
            "Ja", "Trae", "Donovan", "Bam", "Jimmy", "Bradley", "Zion",
            "De'Aaron", "Brandon", "Draymond", "Klay", "Chris", "Russell",
            "Kyrie", "Karl-Anthony", "DeMar",
        ]
        
        last_names = [
            "James", "Curry", "Durant", "Antetokounmpo", "Doncic", "Jokic",
            "Embiid", "Tatum", "Lillard", "Davis", "Harden", "Leonard", "George",
            "Booker", "Morant", "Young", "Mitchell", "Adebayo", "Butler",
            "Beal", "Williamson", "Fox", "Ingram", "Green", "Thompson", "Paul",
            "Westbrook", "Irving", "Towns", "DeRozan",
        ]
        
        positions = ["PG", "SG", "SF", "PF", "C"]
        
        players = []
        for i in range(150):  # Generate 150 players (5 per team)
            team_idx = i % len(self.teams_data)
            first = random.choice(first_names)
            last = random.choice(last_names)
            
            players.append({
                "external_id": f"player_{i+1}",
                "name": f"{first} {last}",
                "position": random.choice(positions),
                "team_external_id": self.teams_data[team_idx]["external_id"],
            })
        
        return players
    
    def get_teams(self) -> list[dict[str, Any]]:
        """Get all NBA teams."""
        logger.info(f"Mock provider: returning {len(self.teams_data)} teams")
        return self.teams_data
    
    def get_players(self) -> list[dict[str, Any]]:
        """Get all NBA players."""
        logger.info(f"Mock provider: returning {len(self.players_data)} players")
        return self.players_data
    
    def get_games(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Generate fake games for date range."""
        games = []
        current_date = start_date
        game_id = 1
        
        while current_date <= end_date:
            # Generate 5-10 games per day
            num_games = random.randint(5, 10)
            
            # Randomly select teams for matchups
            available_teams = self.teams_data.copy()
            random.shuffle(available_teams)
            
            for i in range(min(num_games, len(available_teams) // 2)):
                home_team = available_teams[i * 2]
                away_team = available_teams[i * 2 + 1]
                
                # Generate game context
                spread = round(random.uniform(-12, 12), 1)
                total = round(random.uniform(210, 235), 1)
                
                # Sometimes generate final scores
                if current_date < date.today():
                    status = "final"
                    home_score = random.randint(95, 125)
                    away_score = random.randint(95, 125)
                else:
                    status = "scheduled"
                    home_score = None
                    away_score = None
                
                games.append({
                    "external_id": f"game_{current_date.isoformat()}_{game_id}",
                    "game_date": current_date,
                    "season": "2024-25",
                    "home_team_external_id": home_team["external_id"],
                    "away_team_external_id": away_team["external_id"],
                    "home_score": home_score,
                    "away_score": away_score,
                    "status": status,
                    "spread": spread,
                    "total": total,
                })
                
                game_id += 1
            
            current_date += timedelta(days=1)
        
        logger.info(f"Mock provider: generated {len(games)} games")
        return games
    
    def get_box_scores(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Generate fake box scores for games in date range."""
        games = self.get_games(start_date, end_date)
        
        # Only generate box scores for final games
        final_games = [g for g in games if g["status"] == "final"]
        
        box_scores = []
        
        for game in final_games:
            # Get players from both teams
            home_players = [
                p for p in self.players_data
                if p["team_external_id"] == game["home_team_external_id"]
            ][:8]  # Top 8 players
            
            away_players = [
                p for p in self.players_data
                if p["team_external_id"] == game["away_team_external_id"]
            ][:8]
            
            all_game_players = home_players + away_players
            
            for player in all_game_players:
                # Generate realistic stats
                minutes = round(random.uniform(15, 38), 1)
                points = random.randint(8, 35)
                assists = random.randint(1, 12)
                rebounds = random.randint(2, 15)
                steals = random.randint(0, 3)
                blocks = random.randint(0, 3)
                turnovers = random.randint(0, 5)
                threes = random.randint(0, 6)
                fgm = random.randint(3, 14)
                fga = random.randint(fgm, 25)
                ftm = random.randint(0, 10)
                fta = random.randint(ftm, 12)
                
                team_external_id = player["team_external_id"]
                
                box_scores.append({
                    "game_external_id": game["external_id"],
                    "player_external_id": player["external_id"],
                    "team_external_id": team_external_id,
                    "minutes": minutes,
                    "points": points,
                    "assists": assists,
                    "rebounds": rebounds,
                    "steals": steals,
                    "blocks": blocks,
                    "turnovers": turnovers,
                    "three_pointers_made": threes,
                    "field_goals_made": fgm,
                    "field_goals_attempted": fga,
                    "free_throws_made": ftm,
                    "free_throws_attempted": fta,
                })
        
        logger.info(f"Mock provider: generated {len(box_scores)} box scores")
        return box_scores
