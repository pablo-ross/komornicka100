from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services.source_gpx_service import get_all_source_gpxs


router = APIRouter()


@router.get("/activities/leaderboard", response_model=List[Dict])
async def get_leaderboard(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard with top users by activity count
    """
    # Join with users table to verify that users are active
    leaderboard_entries = (
        db.query(models.Leaderboard.first_name, models.Leaderboard.last_name, models.Leaderboard.activity_count) # Select only needed columns
        .join(models.User, models.User.id == models.Leaderboard.id)
        .filter(models.User.is_active == True)
        .filter(models.Leaderboard.activity_count > 0) # Added filter for activity_count > 0
        .order_by(models.Leaderboard.activity_count.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "first_name": first_name,
            "last_name": last_name[0].upper() + ".",  # Get first letter and add dot
            "activity_count": activity_count
        }
        for first_name, last_name, activity_count in leaderboard_entries
    ]


@router.get("/activities/leaderboard", response_model=List[Dict])
async def get_leaderboard(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard with top users by activity count
    """
    # Join with users table to verify that users are active
    leaderboard_entries = (
        db.query(models.Leaderboard)
        .join(models.User, models.User.id == models.Leaderboard.id)
        .filter(models.User.is_active == True)
        .order_by(models.Leaderboard.activity_count.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "first_name": entry.first_name,
            "last_name": entry.last_name,
            "activity_count": entry.activity_count
        }
        for entry in leaderboard_entries
    ]


@router.get("/activities/user/{user_id}", response_model=List[Dict])
async def get_user_activities(user_id: str, db: Session = Depends(get_db)):
    """
    Get all verified activities for a user
    """
    # Check if user exists and is active
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive"
        )
    
    # Get user's verified activities
    activities = (
        db.query(models.Activity)
        .filter(models.Activity.user_id == user_id)
        .order_by(models.Activity.start_date.desc())
        .all()
    )
    
    # Get source GPX info for each activity
    result = []
    for activity in activities:
        source_gpx = db.query(models.SourceGPX).filter(
            models.SourceGPX.id == activity.source_gpx_id
        ).first()
        
        result.append({
            "id": activity.id,
            "name": activity.name,
            "start_date": activity.start_date.isoformat(),
            "distance_km": round(activity.distance / 1000, 1),
            "duration_seconds": activity.duration,
            "route_name": source_gpx.name if source_gpx else "Unknown route",
            "verified_at": activity.verified_at.isoformat()
        })
    
    return result