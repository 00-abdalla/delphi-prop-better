"""NBA API data provider using nba_api library."""
import time
from datetime import date, datetime, timedelta
from typing import Any

from nba_api.stats.endpoints import boxscoretraditionalv3, scoreboardv2
from nba_api.stats.static import players, teams

from backend.app.logging_config import get_logger
from data_pipeline.ingestion.nba_mock_provider import BaseNBAProvider
from data_pipeline.ingestion.rate_limiter import rate_limited

logger = get_logger(__name__)


class NBAApiProvider(BaseNBAProvider):
    """Real NBA data provider using nba_api."""
    
    def __init__(self, rate_limit_calls_per_minute: int = 18):
        """
        Initialize NBA API provider.
        
        Args:
            rate_limit_calls_per_minute: API calls per minute (default 18 for safety)
        """
        self.rate_limit = rate_limit_calls_per_minute
        self._teams_cache = None
        self._players_cache = None
        logger.info(f"Initialized NBAApiProvider with rate limit: {rate_limit_calls_per_minute} calls/min")
    
    def get_teams(self) -> list[dict[str, Any]]:
        """
        Get all NBA teams from nba_api.
        
        Returns:
            List of team dictionaries with external_id, name, abbrev
        """
        if self._teams_cache is not None:
            logger.info(f"Using cached teams: {len(self._teams_cache)} teams")
            return self._teams_cache
        
        logger.info("Fetching teams from nba_api")
        nba_teams = teams.get_teams()
        
        # Transform to our schema
        teams_data = []
        for team in nba_teams:
            teams_data.append({
                "external_id": str(team["id"]),  # Convert int to string for consistency
                "name": team["full_name"],
                "abbrev": team["abbreviation"],
            })
        
        self._teams_cache = teams_data
        logger.info(f"Fetched {len(teams_data)} teams from NBA API")
        return teams_data
    
    def get_players(self) -> list[dict[str, Any]]:
        """
        Get all active NBA players from nba_api.
        
        Returns:
            List of player dictionaries with external_id, name, team_external_id, position
        """
        if self._players_cache is not None:
            logger.info(f"Using cached players: {len(self._players_cache)} players")
            return self._players_cache
        
        logger.info("Fetching active players from nba_api")
        nba_players = players.get_active_players()
        
        # Transform to our schema
        # Note: nba_api static players don't have team info, we'll get that from box scores
        players_data = []
        for player in nba_players:
            players_data.append({
                "external_id": str(player["id"]),
                "name": player["full_name"],
                "team_external_id": None,  # Will be populated from box scores
                "position": None,  # Will be populated from box scores
            })
        
        self._players_cache = players_data
        logger.info(f"Fetched {len(players_data)} active players from NBA API")
        return players_data
    
    @rate_limited(calls_per_minute=18)
    def _get_scoreboard(self, target_date: date) -> dict:
        """
        Get scoreboard for a specific date (rate limited).
        
        Args:
            target_date: Date to fetch games for
            
        Returns:
            Scoreboard response dictionary
        """
        date_str = target_date.strftime("%Y-%m-%d")
        logger.debug(f"Fetching scoreboard for {date_str}")
        
        try:
            sb = scoreboardv2.ScoreboardV2(game_date=date_str)
            return sb.get_dict()
        except Exception as e:
            logger.error(f"Error fetching scoreboard for {date_str}: {e}")
            return {"resultSets": [{"rowSet": []}]}
    
    @rate_limited(calls_per_minute=18)
    def _get_box_score(self, game_id: str) -> dict:
        """
        Get box score for a specific game (rate limited).
        
        Args:
            game_id: NBA game ID
            
        Returns:
            Box score response dictionary
        """
        logger.debug(f"Fetching box score for game {game_id}")
        
        try:
            # Use V3 since V2 is deprecated
            box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
            return box.get_dict()
        except Exception as e:
            logger.error(f"Error fetching box score for {game_id}: {e}")
            return {"resultSets": [{"rowSet": []}]}
    
    def get_games(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """
        Get games in date range from NBA API.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of game dictionaries
        """
        logger.info(f"Fetching games from {start_date} to {end_date}")
        games = []
        current_date = start_date
        
        while current_date <= end_date:
            scoreboard = self._get_scoreboard(current_date)
            
            # Parse scoreboard response
            game_header = scoreboard.get("resultSets", [{}])[0]
            headers = game_header.get("headers", [])
            rows = game_header.get("rowSet", [])
            
            if not rows:
                logger.debug(f"No games found for {current_date}")
                current_date += timedelta(days=1)
                continue
            
            # Create header index map
            header_map = {h: i for i, h in enumerate(headers)}
            
            for row in rows:
                try:
                    game_id = row[header_map.get("GAME_ID", 2)]
                    game_date_str = row[header_map.get("GAME_DATE_EST", 0)]
                    home_team_id = row[header_map.get("HOME_TEAM_ID", 6)]
                    away_team_id = row[header_map.get("VISITOR_TEAM_ID", 7)]
                    game_status = row[header_map.get("GAME_STATUS_TEXT", 4)]
                    
                    # Parse scores if available
                    home_score = None
                    away_score = None
                    if "PTS_home" in header_map and row[header_map["PTS_home"]]:
                        home_score = int(row[header_map["PTS_home"]])
                    if "PTS_away" in header_map and row[header_map["PTS_away"]]:
                        away_score = int(row[header_map["PTS_away"]])
                    
                    # Determine status
                    status = "scheduled"
                    if "Final" in game_status:
                        status = "final"
                    elif game_status not in ["", " "]:
                        status = "live"
                    
                    # Determine season (simplified - assumes current season)
                    year = current_date.year
                    if current_date.month >= 10:
                        season = f"{year}-{str(year + 1)[2:]}"
                    else:
                        season = f"{year - 1}-{str(year)[2:]}"
                    
                    games.append({
                        "external_id": str(game_id),
                        "game_date": current_date,
                        "season": season,
                        "home_team_external_id": str(home_team_id),
                        "away_team_external_id": str(away_team_id),
                        "home_score": home_score,
                        "away_score": away_score,
                        "status": status,
                        "spread": None,  # Not available from NBA API
                        "total": None,   # Not available from NBA API
                    })
                except (IndexError, ValueError, KeyError) as e:
                    logger.warning(f"Error parsing game row: {e}")
                    continue
            
            current_date += timedelta(days=1)
        
        logger.info(f"Fetched {len(games)} games from NBA API")
        return games
    
    def get_box_scores(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """
        Get box scores for games in date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of box score dictionaries
        """
        logger.info(f"Fetching box scores from {start_date} to {end_date}")
        
        # First get all games in the range
        games = self.get_games(start_date, end_date)
        final_games = [g for g in games if g["status"] == "final"]
        
        logger.info(f"Found {len(final_games)} completed games to fetch box scores for")
        
        all_box_scores = []
        
        for i, game in enumerate(final_games):
            game_id = game["external_id"]
            logger.info(f"Fetching box score {i+1}/{len(final_games)}: {game_id}")
            
            box_score_data = self._get_box_score(game_id)
            
            # Parse box score response - V3 format
            player_stats = box_score_data.get("resultSets", [{}])[0]
            headers = player_stats.get("headers", [])
            rows = player_stats.get("rowSet", [])
            
            if not rows:
                logger.warning(f"No box score data for game {game_id}")
                continue
            
            # Create header index map
            header_map = {h: i for i, h in enumerate(headers)}
            
            for row in rows:
                try:
                    player_id = row[header_map.get("personId", header_map.get("PLAYER_ID", 4))]
                    team_id = row[header_map.get("teamId", header_map.get("TEAM_ID", 1))]
                    
                    # Skip if no player ID (team totals row)
                    if not player_id:
                        continue
                    
                    # Parse minutes (format: "24:30" or "24.5")
                    minutes_val = row[header_map.get("minutes", header_map.get("MIN", 9))]
                    minutes = None
                    if minutes_val:
                        if isinstance(minutes_val, str) and ":" in minutes_val:
                            parts = minutes_val.split(":")
                            minutes = float(parts[0]) + float(parts[1]) / 60
                        else:
                            minutes = float(minutes_val) if minutes_val else None
                    
                    all_box_scores.append({
                        "game_external_id": str(game_id),
                        "player_external_id": str(player_id),
                        "team_external_id": str(team_id),
                        "minutes": minutes,
                        "points": row[header_map.get("points", header_map.get("PTS", 26))],
                        "assists": row[header_map.get("assists", header_map.get("AST", 21))],
                        "rebounds": row[header_map.get("reboundsTotal", header_map.get("REB", 20))],
                        "steals": row[header_map.get("steals", header_map.get("STL", 22))],
                        "blocks": row[header_map.get("blocks", header_map.get("BLK", 23))],
                        "turnovers": row[header_map.get("turnovers", header_map.get("TO", 24))],
                        "three_pointers_made": row[header_map.get("threePointersMade", header_map.get("FG3M", 13))],
                        "field_goals_made": row[header_map.get("fieldGoalsMade", header_map.get("FGM", 10))],
                        "field_goals_attempted": row[header_map.get("fieldGoalsAttempted", header_map.get("FGA", 11))],
                        "free_throws_made": row[header_map.get("freeThrowsMade", header_map.get("FTM", 16))],
                        "free_throws_attempted": row[header_map.get("freeThrowsAttempted", header_map.get("FTA", 17))],
                    })
                except (IndexError, ValueError, KeyError, TypeError) as e:
                    logger.warning(f"Error parsing box score row for game {game_id}: {e}")
                    continue
        
        logger.info(f"Fetched {len(all_box_scores)} box scores from NBA API")
        return all_box_scores
