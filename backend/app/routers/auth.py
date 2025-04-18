from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.config import settings

router = APIRouter()


@router.get("/auth/settings")
def get_public_settings():
    """
    Get public application settings for the frontend
    """
    return {
        "project_name": settings.PROJECT_NAME,
        "strava_client_id": settings.STRAVA_CLIENT_ID,
        "min_activity_distance_km": settings.MIN_ACTIVITY_DISTANCE_KM,
    }