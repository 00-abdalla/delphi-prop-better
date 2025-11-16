"""Backfill historical data job."""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.db import SessionLocal
from backend.app.db.models import BoxScore, Game, Player, StatType, Team
from backend.app.logging_config import get_logger
from data_pipeline.ingestion.nba_mock_provider import NBAMockProvider

logger = get_logger(__name__)


def main():
    """Backfill historical NBA data."""
    logger.info("Starting historical data backfill")
    
    db = SessionLocal()
    provider = NBAMockProvider()
    
    try:
        # Insert stat types first
        logger.info("Creating stat types...")
        stat_types_data = [
            {"name": "points", "display_name": "Points", "abbreviation": "PTS"},
            {"name": "assists", "display_name": "Assists", "abbreviation": "AST"},
            {"name": "rebounds", "display_name": "Rebounds", "abbreviation": "REB"},
        ]
        
        for st_data in stat_types_data:
            existing = db.query(StatType).filter(StatType.name == st_data["name"]).first()
            if not existing:
                st = StatType(**st_data)
                db.add(st)
        
        db.commit()
        logger.info("Stat types created")
        
        # Insert teams
        logger.info("Inserting teams...")
        teams_data = provider.get_teams()
        team_map = {}
        
        for team_data in teams_data:
            existing = db.query(Team).filter(Team.external_id == team_data["external_id"]).first()
            if existing:
                team_map[team_data["external_id"]] = existing.id
            else:
                team = Team(
                    external_id=team_data["external_id"],
                    name=team_data["name"],
                    abbrev=team_data["abbrev"],
                )
                db.add(team)
                db.flush()
                team_map[team_data["external_id"]] = team.id
        
        db.commit()
        logger.info(f"Inserted {len(team_map)} teams")
        
        # Insert players
        logger.info("Inserting players...")
        players_data = provider.get_players()
        player_map = {}
        
        for player_data in players_data:
            existing = db.query(Player).filter(Player.external_id == player_data["external_id"]).first()
            if existing:
                player_map[player_data["external_id"]] = existing.id
            else:
                team_id = team_map.get(player_data["team_external_id"])
                player = Player(
                    external_id=player_data["external_id"],
                    name=player_data["name"],
                    position=player_data.get("position"),
                    team_id=team_id,
                    is_active=True,
                )
                db.add(player)
                db.flush()
                player_map[player_data["external_id"]] = player.id
        
        db.commit()
        logger.info(f"Inserted {len(player_map)} players")
        
        # Insert games and box scores for last 90 days
        start_date = date.today() - timedelta(days=90)
        end_date = date.today() - timedelta(days=1)
        
        logger.info(f"Inserting games from {start_date} to {end_date}...")
        games_data = provider.get_games(start_date, end_date)
        game_map = {}
        
        for game_data in games_data:
            existing = db.query(Game).filter(Game.external_id == game_data["external_id"]).first()
            if existing:
                game_map[game_data["external_id"]] = existing.id
            else:
                game = Game(
                    external_id=game_data["external_id"],
                    game_date=game_data["game_date"],
                    season=game_data["season"],
                    home_team_id=team_map[game_data["home_team_external_id"]],
                    away_team_id=team_map[game_data["away_team_external_id"]],
                    home_score=game_data.get("home_score"),
                    away_score=game_data.get("away_score"),
                    status=game_data["status"],
                    spread=game_data.get("spread"),
                    total=game_data.get("total"),
                )
                db.add(game)
                db.flush()
                game_map[game_data["external_id"]] = game.id
        
        db.commit()
        logger.info(f"Inserted {len(game_map)} games")
        
        # Insert box scores
        logger.info("Inserting box scores...")
        box_scores_data = provider.get_box_scores(start_date, end_date)
        
        for box_score_data in box_scores_data:
            game_id = game_map.get(box_score_data["game_external_id"])
            player_id = player_map.get(box_score_data["player_external_id"])
            team_id = team_map.get(box_score_data["team_external_id"])
            
            if not all([game_id, player_id, team_id]):
                continue
            
            existing = (
                db.query(BoxScore)
                .filter(BoxScore.game_id == game_id)
                .filter(BoxScore.player_id == player_id)
                .first()
            )
            
            if not existing:
                box_score = BoxScore(
                    game_id=game_id,
                    player_id=player_id,
                    team_id=team_id,
                    minutes=box_score_data.get("minutes"),
                    points=box_score_data.get("points"),
                    assists=box_score_data.get("assists"),
                    rebounds=box_score_data.get("rebounds"),
                    steals=box_score_data.get("steals"),
                    blocks=box_score_data.get("blocks"),
                    turnovers=box_score_data.get("turnovers"),
                    three_pointers_made=box_score_data.get("three_pointers_made"),
                    field_goals_made=box_score_data.get("field_goals_made"),
                    field_goals_attempted=box_score_data.get("field_goals_attempted"),
                    free_throws_made=box_score_data.get("free_throws_made"),
                    free_throws_attempted=box_score_data.get("free_throws_attempted"),
                )
                db.add(box_score)
        
        db.commit()
        logger.info(f"Inserted box scores")
        
        logger.info("Historical data backfill complete")
    
    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
