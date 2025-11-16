"""Players API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.services.players_service import PlayersService
from backend.app.core.services.props_service import PropsService
from backend.app.db.session import get_db

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/search")
def search_players(
    q: str = Query(..., description="Search query (player name)", min_length=2),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search for players by name."""
    service = PlayersService(db)
    results = service.search_players(query=q, limit=limit)
    
    return {
        "query": q,
        "count": len(results),
        "players": results,
    }


@router.get("/{player_id}")
def get_player(
    player_id: int,
    db: Session = Depends(get_db),
):
    """Get player details by ID."""
    service = PlayersService(db)
    player = service.get_player_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return player


@router.get("/{player_id}/props")
def get_player_props(
    player_id: int,
    db: Session = Depends(get_db),
):
    """Get all current props for a player."""
    # Verify player exists
    players_service = PlayersService(db)
    player = players_service.get_player_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get props
    props_service = PropsService(db)
    props = props_service.get_props_for_player(player_id)
    
    return {
        "player": player,
        "count": len(props),
        "props": props,
    }


@router.get("/")
def list_players(
    limit: int = Query(500, description="Maximum number of results", ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all active players."""
    service = PlayersService(db)
    players = service.get_all_active_players(limit=limit)
    
    return {
        "count": len(players),
        "players": players,
    }
