"""Games API routes."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.services.games_service import GamesService
from backend.app.core.services.props_service import PropsService
from backend.app.db.session import get_db

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/date/{target_date}")
def get_games_by_date(
    target_date: str,
    db: Session = Depends(get_db),
):
    """Get all games for a specific date."""
    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    service = GamesService(db)
    games = service.get_games_by_date(parsed_date)
    
    return {
        "date": target_date,
        "count": len(games),
        "games": games,
    }


@router.get("/upcoming")
def get_upcoming_games(
    limit: int = Query(50, description="Maximum number of results", ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get upcoming games."""
    service = GamesService(db)
    games = service.get_upcoming_games(limit=limit)
    
    return {
        "count": len(games),
        "games": games,
    }


@router.get("/{game_id}")
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
):
    """Get game details by ID."""
    service = GamesService(db)
    game = service.get_game_by_id(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game


@router.get("/{game_id}/props")
def get_game_props(
    game_id: int,
    db: Session = Depends(get_db),
):
    """Get all props for a specific game."""
    # Verify game exists
    games_service = GamesService(db)
    game = games_service.get_game_by_id(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get props
    props_service = PropsService(db)
    props = props_service.get_props_for_game(game_id)
    
    return {
        "game": game,
        "count": len(props),
        "props": props,
    }
