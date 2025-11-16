"""Tests for props service."""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.services.props_service import PropsService
from backend.app.db.base import Base
from backend.app.db.models import (
    Game,
    OddsSnapshot,
    Player,
    Prop,
    PropPrediction,
    StatType,
    Team,
)


@pytest.fixture
def db_session():
    """Create in-memory test database with sample data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create test data
    team = Team(external_id="LAL", name="Lakers", abbrev="LAL")
    session.add(team)
    session.flush()
    
    player = Player(external_id="player1", name="Test Player", team_id=team.id, position="PG")
    session.add(player)
    session.flush()
    
    stat_type = StatType(name="points", display_name="Points", abbreviation="PTS")
    session.add(stat_type)
    session.flush()
    
    game = Game(
        external_id="game1",
        game_date=date.today(),
        season="2024-25",
        home_team_id=team.id,
        away_team_id=team.id,
        status="scheduled",
    )
    session.add(game)
    session.flush()
    
    prop = Prop(
        game_id=game.id,
        player_id=player.id,
        stat_type_id=stat_type.id,
        sportsbook="fanduel",
        line=25.5,
        prop_date=date.today(),
        is_active=True,
    )
    session.add(prop)
    session.flush()
    
    odds = OddsSnapshot(
        prop_id=prop.id,
        over_odds=-110,
        under_odds=-110,
    )
    session.add(odds)
    
    prediction = PropPrediction(
        prop_id=prop.id,
        model_name="test_model",
        run_id="test_run",
        predicted_mean=27.5,
        predicted_variance=16.0,
        prob_over=0.60,
        prob_under=0.40,
        edge_over=0.08,
        edge_under=-0.12,
        ev_over=0.05,
        ev_under=-0.08,
    )
    session.add(prediction)
    session.commit()
    
    yield session
    session.close()


def test_get_top_props(db_session):
    """Test getting top props."""
    service = PropsService(db_session)
    
    props = service.get_top_props(stat_type="points", min_edge=0.05, limit=10)
    
    assert len(props) >= 1
    assert props[0]["player_name"] == "Test Player"
    assert props[0]["edge"] >= 0.05


def test_get_props_for_player(db_session):
    """Test getting props for a player."""
    service = PropsService(db_session)
    
    player = db_session.query(Player).first()
    props = service.get_props_for_player(player.id)
    
    assert len(props) >= 1
    assert props[0]["stat_type"] == "points"
    assert "predicted_mean" in props[0]


def test_get_props_for_game(db_session):
    """Test getting props for a game."""
    service = PropsService(db_session)
    
    game = db_session.query(Game).first()
    props = service.get_props_for_game(game.id)
    
    assert len(props) >= 1
    assert props[0]["player_name"] == "Test Player"
    assert "best_edge" in props[0]
