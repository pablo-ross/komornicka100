import logging
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any

from sqlalchemy.orm import Session

from models import User, Activity, ActivityAttempt, SourceGPX
from services import (
    ensure_fresh_token, 
    get_activity_by_id, 
    get_activity_streams,
    load_source_gpx_file,
    convert_strava_streams_to_points,
    verify_activity_against_source,
    update_leaderboard,
    send_activity_verification_email
)

# Configure logging
logger = logging.getLogger("kmtb-worker")

async def verify_strava_activity(
    db: Session,
    user_id: str,
    activity_id: str,
    source_gpx_id: str = None
) -> Dict[str, any]:
    """Verify a Strava activity against a source GPX file"""
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
    else:
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
    """Verify activity against a specific source GPX"""
    # Get source GPX
    source_gpx = db.query(SourceGPX).filter(
        SourceGPX.id == source_gpx_id,
        SourceGPX.is_active == True
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
    activity_attempt = ActivityAttempt(
        id=uuid.uuid4(),
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
        existing = db.query(Activity).filter(
            Activity.strava_activity_id == activity_id
        ).first()
        
        if not existing:
            # Add new approved activity
            new_activity = Activity(
                id=uuid.uuid4(),
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
            
            # Send verification email
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                send_activity_verification_email(
                    user.email,
                    user.first_name,
                    activity_details.get("name", "Unknown Activity"),
                    activity_details.get("start_date_local", "Unknown date"),
                    source_gpx.name
                )
    
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
    """Verify activity against all active source GPXs"""
    # Get all active source GPXs
    source_gpxs = db.query(SourceGPX).filter(
        SourceGPX.is_active == True
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
            logger.warning(f"Failed to load source GPX file {source_gpx.filename}: {content}")
            continue
        
        # Verify activity against source
        verification_result = verify_activity_against_source(
            content, activity_points, activity_distance
        )
        
        # Record verification attempt
        activity_attempt = ActivityAttempt(
            id=uuid.uuid4(),
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
        existing = db.query(Activity).filter(
            Activity.strava_activity_id == activity_id
        ).first()
        
        if not existing:
            # Add new approved activity
            new_activity = Activity(
                id=uuid.uuid4(),
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
            
            # Send verification email
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                send_activity_verification_email(
                    user.email,
                    user.first_name,
                    activity_details.get("name", "Unknown Activity"),
                    activity_details.get("start_date_local", "Unknown date"),
                    best_result["source_gpx"]["name"]
                )
    
    db.commit()
    
    return {
        "success": True,
        **best_result
    }