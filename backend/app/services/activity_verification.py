from datetime import datetime
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from .. import models
from ..core.config import settings
from .gpx_comparison import convert_strava_streams_to_points, verify_activity_against_source
from .source_gpx_service import load_source_gpx_file
from .strava_service import (
    ensure_fresh_token, 
    get_activity_by_id, 
    get_activity_streams
)


async def verify_strava_activity(
    db: Session,
    user_id: str,
    activity_id: str,
    source_gpx_id: str = None
) -> Dict[str, any]:
    """
    Verify a Strava activity against a source GPX file
    
    Args:
        db: Database session
        user_id: User ID
        activity_id: Strava activity ID
        source_gpx_id: Optional source GPX ID (if None, check against all active sources)
        
    Returns:
        Dict with verification results
    """
    # Ensure fresh token
    token_success, token_value = await ensure_fresh_token(db, user_id)
    if not token_success:
        return {
            "success": False,
            "message": f"Failed to get valid token: {token_value}"
        }
    
    # Get activity details
    activity_details = await get_activity_by_id(token_value, activity_id)
    if "error" in activity_details:
        return {
            "success": False,
            "message": f"Failed to get activity details: {activity_details.get('error')}"
        }
    
    # Check if activity is a ride
    if activity_details.get("type") != "Ride":
        return {
            "success": False,
            "message": f"Activity is not a bike ride (type: {activity_details.get('type')})"
        }
    
    # Get activity streams (GPS data)
    streams = await get_activity_streams(token_value, activity_id)
    if "error" in streams:
        return {
            "success": False,
            "message": f"Failed to get activity streams: {streams.get('error')}"
        }
    
    # Convert streams to points
    activity_points = convert_strava_streams_to_points(streams)
    if not activity_points:
        return {
            "success": False,
            "message": "No GPS data found in activity"
        }
    
    # Get activity distance
    activity_distance = activity_details.get("distance", 0)  # in meters
    
    # If source_gpx_id provided, verify against that specific source
    if source_gpx_id:
        return await verify_against_specific_source(
            db, user_id, activity_id, source_gpx_id, 
            activity_details, activity_points, activity_distance
        )
    
    # If no source_gpx_id provided, check against all active sources
    return await verify_against_all_sources(
        db, user_id, activity_id, 
        activity_details, activity_points, activity_distance
    )


async def verify_against_specific_source(
    db: Session,
    user_id: str,
    activity_id: str,
    source_gpx_id: str,
    activity_details: Dict[str, any],
    activity_points: List[Tuple[float, float]],
    activity_distance: float
) -> Dict[str, any]:
    """
    Verify activity against a specific source GPX
    """
    # Get source GPX
    source_gpx = db.query(models.SourceGPX).filter(
        models.SourceGPX.id == source_gpx_id,
        models.SourceGPX.is_active == True
    ).first()
    
    if not source_gpx:
        return {
            "success": False,
            "message": f"Source GPX with ID {source_gpx_id} not found or inactive"
        }
    
    # Load source GPX file
    load_success, content = await load_source_gpx_file(source_gpx.filename)
    if not load_success:
        return {
            "success": False,
            "message": f"Failed to load source GPX file: {content}"
        }
    
    # Verify activity against source
    verification_result = verify_activity_against_source(
        content, activity_points, activity_distance
    )
    
    # Record verification attempt
    activity_attempt = models.ActivityAttempt(
        user_id=user_id,
        strava_activity_id=activity_id,
        source_gpx_id=source_gpx_id,
        name=activity_details.get("name", "Unknown Activity"),
        distance=activity_distance,
        duration=activity_details.get("elapsed_time", 0),
        start_date=datetime.fromisoformat(activity_details.get("start_date").replace("Z", "+00:00")),
        is_verified=verification_result["verified"],
        similarity_score=verification_result["similarity_score"],
        verification_message=verification_result["message"]
    )
    
    db.add(activity_attempt)
    
    # If verified, record as approved activity
    if verification_result["verified"]:
        # Check if already recorded
        existing = db.query(models.Activity).filter(
            models.Activity.strava_activity_id == activity_id
        ).first()
        
        if not existing:
            # Add new approved activity
            new_activity = models.Activity(
                user_id=user_id,
                strava_activity_id=activity_id,
                source_gpx_id=source_gpx_id,
                name=activity_details.get("name", "Unknown Activity"),
                distance=activity_distance,
                duration=activity_details.get("elapsed_time", 0),
                start_date=datetime.fromisoformat(activity_details.get("start_date").replace("Z", "+00:00")),
                similarity_score=verification_result["similarity_score"]
            )
            
            db.add(new_activity)
            
            # Update leaderboard
            await update_leaderboard(db, user_id)
    
    db.commit()
    
    return {
        "success": True,
        "verified": verification_result["verified"],
        "similarity_score": verification_result["similarity_score"],
        "message": verification_result["message"],
        "source_gpx": {
            "id": source_gpx.id,
            "name": source_gpx.name
        }
    }


async def verify_against_all_sources(
    db: Session,
    user_id: str,
    activity_id: str,
    activity_details: Dict[str, any],
    activity_points: List[Tuple[float, float]],
    activity_distance: float
) -> Dict[str, any]:
    """
    Verify activity against all active source GPXs
    """
    # Get all active source GPXs
    source_gpxs = db.query(models.SourceGPX).filter(
        models.SourceGPX.is_active == True
    ).all()
    
    if not source_gpxs:
        return {
            "success": False,
            "message": "No active source GPX routes found"
        }
    
    best_result = {
        "verified": False,
        "similarity_score": 0.0,
        "message": "Not matching any route",
        "source_gpx": None
    }
    
    # Check against each source
    for source_gpx in source_gpxs:
        # Load source GPX file
        load_success, content = await load_source_gpx_file(source_gpx.filename)
        if not load_success:
            print(f"Failed to load source GPX file {source_gpx.filename}: {content}")
            continue
        
        # Verify activity against source
        verification_result = verify_activity_against_source(
            content, activity_points, activity_distance
        )
        
        # Record verification attempt
        activity_attempt = models.ActivityAttempt(
            user_id=user_id,
            strava_activity_id=activity_id,
            source_gpx_id=source_gpx.id,
            name=activity_details.get("name", "Unknown Activity"),
            distance=activity_distance,
            duration=activity_details.get("elapsed_time", 0),
            start_date=datetime.fromisoformat(activity_details.get("start_date").replace("Z", "+00:00")),
            is_verified=verification_result["verified"],
            similarity_score=verification_result["similarity_score"],
            verification_message=verification_result["message"]
        )
        
        db.add(activity_attempt)
        
        # Keep track of best match
        if verification_result["similarity_score"] > best_result["similarity_score"]:
            best_result = {
                "verified": verification_result["verified"],
                "similarity_score": verification_result["similarity_score"],
                "message": verification_result["message"],
                "source_gpx": {
                    "id": source_gpx.id,
                    "name": source_gpx.name
                }
            }
    
    # If verified, record as approved activity
    if best_result["verified"]:
        # Check if already recorded
        existing = db.query(models.Activity).filter(
            models.Activity.strava_activity_id == activity_id
        ).first()
        
        if not existing:
            # Add new approved activity
            new_activity = models.Activity(
                user_id=user_id,
                strava_activity_id=activity_id,
                source_gpx_id=best_result["source_gpx"]["id"],
                name=activity_details.get("name", "Unknown Activity"),
                distance=activity_distance,
                duration=activity_details.get("elapsed_time", 0),
                start_date=datetime.fromisoformat(activity_details.get("start_date").replace("Z", "+00:00")),
                similarity_score=best_result["similarity_score"]
            )
            
            db.add(new_activity)
            
            # Update leaderboard
            await update_leaderboard(db, user_id)
    
    db.commit()
    
    return {
        "success": True,
        **best_result
    }


async def update_leaderboard(db: Session, user_id: str) -> None:
    """
    Update leaderboard entry for user
    
    Args:
        db: Database session
        user_id: User ID
    """
    # Get user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return
    
    # Count approved activities
    activity_count = db.query(models.Activity).filter(
        models.Activity.user_id == user_id
    ).count()
    
    # Update or create leaderboard entry
    leaderboard_entry = db.query(models.Leaderboard).filter(
        models.Leaderboard.id == user_id
    ).first()
    
    if leaderboard_entry:
        leaderboard_entry.activity_count = activity_count
        leaderboard_entry.last_updated = datetime.now()
    else:
        new_entry = models.Leaderboard(
            id=user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            activity_count=activity_count,
            last_updated=datetime.now()
        )
        db.add(new_entry)
    
    db.commit()