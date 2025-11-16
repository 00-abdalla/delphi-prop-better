"""Database models using SQLAlchemy 2.x ORM."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Team(Base):
    """NBA team."""
    
    __tablename__ = "teams"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    abbrev: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    home_games: Mapped[list["Game"]] = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games: Mapped[list["Game"]] = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    players: Mapped[list["Player"]] = relationship("Player", back_populates="team")


class Player(Base):
    """NBA player."""
    
    __tablename__ = "players"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    position: Mapped[Optional[str]] = mapped_column(String(10))
    team_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="players")
    box_scores: Mapped[list["BoxScore"]] = relationship("BoxScore", back_populates="player")
    injury_reports: Mapped[list["InjuryReport"]] = relationship("InjuryReport", back_populates="player")
    props: Mapped[list["Prop"]] = relationship("Prop", back_populates="player")
    game_features: Mapped[list["PlayerGameFeatures"]] = relationship("PlayerGameFeatures", back_populates="player")


class Game(Base):
    """NBA game."""
    
    __tablename__ = "games"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    game_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    season: Mapped[str] = mapped_column(String(20), nullable=False)
    home_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    home_score: Mapped[Optional[int]] = mapped_column(Integer)
    away_score: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled, live, final
    spread: Mapped[Optional[float]] = mapped_column(Float)  # home team perspective
    total: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    box_scores: Mapped[list["BoxScore"]] = relationship("BoxScore", back_populates="game")
    props: Mapped[list["Prop"]] = relationship("Prop", back_populates="game")
    game_features: Mapped[list["PlayerGameFeatures"]] = relationship("PlayerGameFeatures", back_populates="game")


class BoxScore(Base):
    """Player box score for a game."""
    
    __tablename__ = "box_scores"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    minutes: Mapped[Optional[float]] = mapped_column(Float)
    points: Mapped[Optional[int]] = mapped_column(Integer)
    assists: Mapped[Optional[int]] = mapped_column(Integer)
    rebounds: Mapped[Optional[int]] = mapped_column(Integer)
    steals: Mapped[Optional[int]] = mapped_column(Integer)
    blocks: Mapped[Optional[int]] = mapped_column(Integer)
    turnovers: Mapped[Optional[int]] = mapped_column(Integer)
    three_pointers_made: Mapped[Optional[int]] = mapped_column(Integer)
    field_goals_made: Mapped[Optional[int]] = mapped_column(Integer)
    field_goals_attempted: Mapped[Optional[int]] = mapped_column(Integer)
    free_throws_made: Mapped[Optional[int]] = mapped_column(Integer)
    free_throws_attempted: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="box_scores")
    player: Mapped["Player"] = relationship("Player", back_populates="box_scores")


class InjuryReport(Base):
    """Player injury report."""
    
    __tablename__ = "injury_reports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # out, doubtful, questionable, probable, available
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="injury_reports")


class StatType(Base):
    """Canonical stat types (PTS, AST, REB, PRA, etc.)."""
    
    __tablename__ = "stat_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # points, assists, rebounds, etc.
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prop_markets: Mapped[list["PropMarket"]] = relationship("PropMarket", back_populates="stat_type")
    props: Mapped[list["Prop"]] = relationship("Prop", back_populates="stat_type")
    game_features: Mapped[list["PlayerGameFeatures"]] = relationship("PlayerGameFeatures", back_populates="stat_type")


class PropMarket(Base):
    """Mapping of sportsbook market names to canonical stat types."""
    
    __tablename__ = "prop_markets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sportsbook: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # fanduel, draftkings, etc.
    market_name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Player Points", etc.
    stat_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("stat_types.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stat_type: Mapped["StatType"] = relationship("StatType", back_populates="prop_markets")


class Prop(Base):
    """A specific player prop at a sportsbook."""
    
    __tablename__ = "props"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    stat_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("stat_types.id"), nullable=False, index=True)
    sportsbook: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    line: Mapped[float] = mapped_column(Float, nullable=False)
    prop_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="props")
    player: Mapped["Player"] = relationship("Player", back_populates="props")
    stat_type: Mapped["StatType"] = relationship("StatType", back_populates="props")
    odds_snapshots: Mapped[list["OddsSnapshot"]] = relationship("OddsSnapshot", back_populates="prop")
    predictions: Mapped[list["PropPrediction"]] = relationship("PropPrediction", back_populates="prop")


class OddsSnapshot(Base):
    """Time-stamped odds for a prop."""
    
    __tablename__ = "odds_snapshots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prop_id: Mapped[int] = mapped_column(Integer, ForeignKey("props.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, server_default=func.now())
    over_odds: Mapped[int] = mapped_column(Integer, nullable=False)  # American odds
    under_odds: Mapped[int] = mapped_column(Integer, nullable=False)  # American odds
    
    # Relationships
    prop: Mapped["Prop"] = relationship("Prop", back_populates="odds_snapshots")


class PlayerGameFeatures(Base):
    """Engineered features for a player/game/stat combination."""
    
    __tablename__ = "player_game_features"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    stat_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("stat_types.id"), nullable=False, index=True)
    feature_schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    feature_vector: Mapped[dict] = mapped_column(JSON, nullable=False)  # Flexible JSON storage
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="game_features")
    game: Mapped["Game"] = relationship("Game", back_populates="game_features")
    stat_type: Mapped["StatType"] = relationship("StatType", back_populates="game_features")


class PropPrediction(Base):
    """Model prediction for a prop."""
    
    __tablename__ = "prop_predictions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prop_id: Mapped[int] = mapped_column(Integer, ForeignKey("props.id"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    predicted_mean: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_variance: Mapped[float] = mapped_column(Float, nullable=False)
    prob_over: Mapped[float] = mapped_column(Float, nullable=False)
    prob_under: Mapped[float] = mapped_column(Float, nullable=False)
    edge_over: Mapped[float] = mapped_column(Float, nullable=False)
    edge_under: Mapped[float] = mapped_column(Float, nullable=False)
    ev_over: Mapped[float] = mapped_column(Float, nullable=False)
    ev_under: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    prop: Mapped["Prop"] = relationship("Prop", back_populates="predictions")


class PostedPlay(Base):
    """Tracking of posted/recommended plays for performance analysis."""
    
    __tablename__ = "posted_plays"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prop_id: Mapped[int] = mapped_column(Integer, ForeignKey("props.id"), nullable=False, index=True)
    prediction_id: Mapped[int] = mapped_column(Integer, ForeignKey("prop_predictions.id"), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # over, under
    odds_at_post: Mapped[int] = mapped_column(Integer, nullable=False)
    edge_at_post: Mapped[float] = mapped_column(Float, nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    result: Mapped[Optional[str]] = mapped_column(String(10))  # win, loss, push, null if not yet graded
    actual_value: Mapped[Optional[float]] = mapped_column(Float)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
