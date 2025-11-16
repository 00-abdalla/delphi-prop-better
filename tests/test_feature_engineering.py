"""Tests for feature engineering."""
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.models import BoxScore, Game, Player, StatType, Team
from data_pipeline.transform.feature_engineering import FeatureEngineer


@pytest.fixture
def db_session():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create test data
    team = Team(external_id="LAL", name="Lakers", abbrev="LAL")
    session.add(team)
    session.flush()
    
    player = Player(external_id="player1", name="Test Player", team_id=team.id)
    session.add(player)
    session.flush()
    
    stat_type = StatType(name="points", display_name="Points", abbreviation="PTS")
    session.add(stat_type)
    session.flush()
    
    # Create historical games
    for i in range(10):
        game_date = date.today() - timedelta(days=10-i)
        game = Game(
            external_id=f"game_{i}",
            game_date=game_date,
            season="2024-25",
            home_team_id=team.id,
            away_team_id=team.id,
            status="final",
        )
        session.add(game)
        session.flush()
        
        # Add box score
        box_score = BoxScore(
            game_id=game.id,
            player_id=player.id,
            team_id=team.id,
            minutes=30 + i,
            points=20 + i,
            assists=5,
            rebounds=8,
        )
        session.add(box_score)
    
    # Create future game
    future_game = Game(
        external_id="future_game",
        game_date=date.today(),
        season="2024-25",
        home_team_id=team.id,
        away_team_id=team.id,
        status="scheduled",
        spread=-3.5,
        total=220.0,
    )
    session.add(future_game)
    session.commit()
    
    yield session
    
    session.close()


def test_feature_engineer_basic(db_session):
    """Test basic feature engineering."""
    engineer = FeatureEngineer(db_session)
    
    # Build features for today
    engineer.build_player_game_features_for_date(date.today())
    
    # Verify features were created
    from backend.app.db.models import PlayerGameFeatures
    features = db_session.query(PlayerGameFeatures).all()
    
    assert len(features) > 0
    
    # Check feature vector structure
    for feature in features:
        fv = feature.feature_vector
        assert "points_mean_3" in fv or "assists_mean_3" in fv or "rebounds_mean_3" in fv
        assert "minutes_projected" in fv
        assert "spread" in fv
        assert "total" in fv
