"""Daily update job - fetch today's games, props, build features, score."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import settings
from backend.app.db import SessionLocal
from backend.app.db.models import Game, InjuryReport, OddsSnapshot, Player, Prop, StatType, Team
from backend.app.logging_config import get_logger
from data_pipeline.ingestion.injuries_mock_provider import InjuriesMockProvider
from data_pipeline.ingestion.odds_mock_provider import OddsMockProvider
from data_pipeline.ingestion.provider_factory import get_nba_provider
from data_pipeline.transform.feature_engineering import FeatureEngineer
from ml.inference.model_registry import ModelRegistry
from ml.inference.scorer import PropScorer

logger = get_logger(__name__)


def main():
    """Run daily update pipeline."""
    logger.info("Starting daily update job")
    
    target_date = date.today()
    db = SessionLocal()
    
    try:
        # Initialize providers
        nba_provider = get_nba_provider()
        odds_provider = OddsMockProvider()
        injury_provider = InjuriesMockProvider()
        
        # Step 1: Fetch today's games
        logger.info(f"Fetching games for {target_date}")
        games_data = nba_provider.get_games(target_date, target_date)
        
        team_map = {t.external_id: t.id for t in db.query(Team).all()}
        player_map = {p.external_id: p.id for p in db.query(Player).all()}
        stat_type_map = {st.name: st.id for st in db.query(StatType).all()}
        
        game_map = {}
        for game_data in games_data:
            existing = db.query(Game).filter(Game.external_id == game_data["external_id"]).first()
            if not existing:
                game = Game(
                    external_id=game_data["external_id"],
                    game_date=game_data["game_date"],
                    season=game_data["season"],
                    home_team_id=team_map[game_data["home_team_external_id"]],
                    away_team_id=team_map[game_data["away_team_external_id"]],
                    status=game_data["status"],
                    spread=game_data.get("spread"),
                    total=game_data.get("total"),
                )
                db.add(game)
                db.flush()
                game_map[game_data["external_id"]] = game.id
            else:
                game_map[game_data["external_id"]] = existing.id
        
        db.commit()
        logger.info(f"Processed {len(game_map)} games")
        
        # Step 2: Fetch injury reports
        logger.info("Fetching injury reports")
        injuries_data = injury_provider.get_injury_reports(target_date)
        
        for injury_data in injuries_data:
            player_id = player_map.get(injury_data["player_external_id"])
            if player_id:
                injury = InjuryReport(
                    player_id=player_id,
                    report_date=injury_data["report_date"],
                    status=injury_data["status"],
                    description=injury_data.get("description"),
                )
                db.add(injury)
        
        db.commit()
        logger.info(f"Processed {len(injuries_data)} injury reports")
        
        # Step 3: Fetch props and odds
        logger.info("Fetching props and odds")
        
        # Prepare games with players for odds provider
        games_with_players = []
        for game_ext_id, game_id in game_map.items():
            game = db.query(Game).filter(Game.id == game_id).first()
            home_players = db.query(Player).filter(Player.team_id == game.home_team_id).limit(10).all()
            away_players = db.query(Player).filter(Player.team_id == game.away_team_id).limit(10).all()
            
            games_with_players.append({
                "external_id": game_ext_id,
                "game_date": game.game_date,
                "players": [{"external_id": p.external_id} for p in home_players + away_players],
            })
        
        props_data = odds_provider.get_props_for_games(games_with_players)
        
        for prop_data in props_data:
            game_id = game_map.get(prop_data["game_external_id"])
            player_id = player_map.get(prop_data["player_external_id"])
            stat_type_id = stat_type_map.get(prop_data["stat_type"])
            
            if not all([game_id, player_id, stat_type_id]):
                continue
            
            # Create or update prop
            prop = Prop(
                game_id=game_id,
                player_id=player_id,
                stat_type_id=stat_type_id,
                sportsbook=prop_data["sportsbook"],
                line=prop_data["line"],
                prop_date=prop_data["prop_date"],
                is_active=True,
            )
            db.add(prop)
            db.flush()
            
            # Add odds snapshot
            odds_snapshot = OddsSnapshot(
                prop_id=prop.id,
                over_odds=prop_data["over_odds"],
                under_odds=prop_data["under_odds"],
            )
            db.add(odds_snapshot)
        
        db.commit()
        logger.info(f"Processed {len(props_data)} props")
        
        # Step 4: Build features
        logger.info("Building features")
        feature_engineer = FeatureEngineer(db)
        feature_engineer.build_player_game_features_for_date(target_date)
        
        # Step 5: Score props
        logger.info("Scoring props")
        model_registry = ModelRegistry(settings.MODEL_DIR)
        scorer = PropScorer(db, model_registry)
        scorer.score_props_for_date(target_date)
        
        logger.info("Daily update job complete")
    
    except Exception as e:
        logger.error(f"Error during daily update: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
