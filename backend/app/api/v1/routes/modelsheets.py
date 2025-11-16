"""Model sheets API routes."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.services.props_service import PropsService
from backend.app.db.session import get_db

router = APIRouter(prefix="/modelsheets", tags=["modelsheets"])


@router.get("/{target_date}")
def get_model_sheet(
    target_date: str,
    db: Session = Depends(get_db),
):
    """
    Get full model sheet for a date.
    
    Returns all props with predictions across all stat types.
    """
    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    service = PropsService(db)
    
    # Get top props for each stat type
    stat_types = ["points", "assists", "rebounds"]
    
    model_sheet = {
        "date": target_date,
        "stat_types": {},
    }
    
    for stat_type in stat_types:
        props = service.get_top_props(
            stat_type=stat_type,
            min_edge=0.0,  # Include all props
            limit=200,
            target_date=parsed_date,
        )
        model_sheet["stat_types"][stat_type] = {
            "count": len(props),
            "props": props,
        }
    
    return model_sheet
