"""Props API routes."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.services.props_service import PropsService
from backend.app.db.session import get_db

router = APIRouter(prefix="/props", tags=["props"])


@router.get("/top")
def get_top_props(
    stat_type: str = Query("points", description="Stat type: points, assists, rebounds"),
    min_edge: float = Query(0.05, description="Minimum edge threshold", ge=0.0, le=1.0),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=200),
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db),
):
    """
    Get top prop edges by stat type.
    
    Returns props sorted by edge (model prob - book prob).
    """
    service = PropsService(db)
    
    # Parse date if provided
    parsed_date = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    results = service.get_top_props(
        stat_type=stat_type,
        min_edge=min_edge,
        limit=limit,
        target_date=parsed_date,
    )
    
    return {
        "stat_type": stat_type,
        "min_edge": min_edge,
        "count": len(results),
        "props": results,
    }


@router.get("/player/{player_id}")
def get_player_props(
    player_id: int,
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db),
):
    """Get all props for a specific player."""
    service = PropsService(db)
    
    # Parse date if provided
    parsed_date = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    results = service.get_props_for_player(player_id=player_id, target_date=parsed_date)
    
    if not results:
        raise HTTPException(status_code=404, detail="No props found for this player")
    
    return {
        "player_id": player_id,
        "count": len(results),
        "props": results,
    }


@router.get("/game/{game_id}")
def get_game_props(
    game_id: int,
    db: Session = Depends(get_db),
):
    """Get all props for a specific game."""
    service = PropsService(db)
    
    results = service.get_props_for_game(game_id=game_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="No props found for this game")
    
    return {
        "game_id": game_id,
        "count": len(results),
        "props": results,
    }
