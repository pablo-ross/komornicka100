import logging
import math
import smtplib
import ssl
import time
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import gpxpy
import gpxpy.gpx
import httpx
from shapely.geometry import LineString, Point
from sqlalchemy.orm import Session

from models import User, Activity, ActivityAttempt, Token, SourceGPX, Leaderboard
from settings import settings

# Configure logging
logger = logging.getLogger("kmtb-worker")

# Email service functions
def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
) -> bool:
    """Send an email using the configured SMTP server"""
    # Create message container
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USERNAME
    msg["To"] = to_email
    
    # Add CC recipients if provided
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
        
    # Set recipients list for sending
    recipients = [to_email]
    if cc_emails:
        recipients.extend(cc_emails)
    if bcc_emails:
        recipients.extend(bcc_emails)
        
    # Attach HTML part
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)
    
    # Create secure SSL context
    context = ssl.create_default_context()
    
    try:
        # Connect to server and send email
        if settings.SMTP_PORT == 1025:  # For Mailpit testing (no auth, no SSL/TLS)
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.sendmail(settings.SMTP_USERNAME, recipients, msg.as_string())
        elif settings.SMTP_PORT == 465:  # For SSL connections
            with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as server:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USERNAME, recipients, msg.as_string())
        else:  # For TLS connections (usually port 587)
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USERNAME, recipients, msg.as_string())
        return True
    except Exception as e:
        # Log the error
        logger.error(f"Error sending email: {e}")
        return False

def send_activity_verification_email(
    to_email: str,
    first_name: str,
    activity_name: str,
    activity_date: str,
    source_gpx_name: str,
) -> bool:
    """Send an email notification about a verified activity"""
    subject = f"{settings.PROJECT_NAME} - Activity Verified!"
    content = f"""
    <html>
    <body>
        <h1>Hello {first_name},</h1>
        <p>Good news! Your activity has been verified for the {settings.PROJECT_NAME}.</p>
        <p><strong>Activity:</strong> {activity_name}</p>
        <p><strong>Date:</strong> {activity_date}</p>
        <p><strong>Route:</strong> {source_gpx_name}</p>
        <p>This activity has been added to your contest profile. Keep up the great work!</p>
        <p>Best regards,<br>{settings.PROJECT_NAME} Team</p>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, content)

# Strava API functions
async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh Strava access token using refresh token"""
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": settings.STRAVA_CLIENT_ID,
        "client_secret": settings.STRAVA_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            return response.json()
    except Exception as e:
        logger.error(f"Error refreshing access token: {e}")
        return {"error": str(e)}

async def ensure_fresh_token(db: Session, user_id: str) -> Tuple[bool, str]:
    """Ensure the user has a fresh Strava access token"""
    # Get token from database
    token = db.query(Token).filter(Token.user_id == user_id).first()
    
    if not token:
        return False, "No token found"
    
    current_time = int(time.time())
    
    # Check if token is expired or about to expire (within 5 minutes)
    if token.expires_at <= current_time + 300:
        # Refresh the token
        token_response = await refresh_access_token(token.refresh_token)
        
        if "error" in token_response:
            return False, token_response["error"]
        
        # Update token in database
        token.access_token = token_response["access_token"]
        token.refresh_token = token_response["refresh_token"]
        token.expires_at = token_response["expires_at"]
        token.updated_at = datetime.now()
        
        db.commit()
        
        return True, token.access_token
    
    # Token is still valid
    return True, token.access_token

async def get_activities_after_date(
    access_token: str, 
    after_timestamp: int,
    activity_type: str = "Ride",
    page: int = 1,
    per_page: int = 30
) -> List[Dict[str, Any]]:
    """Get activities from Strava API after a specific date"""
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "after": after_timestamp,
        "page": page,
        "per_page": per_page
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            activities = response.json()
            
            # Filter activities by type
            if activities and isinstance(activities, list):
                return [a for a in activities if a.get("type") == activity_type]
            return []
    except Exception as e:
        logger.error(f"Error getting activities: {e}")
        return []

async def get_activity_by_id(
    access_token: str, 
    activity_id: str
) -> Dict[str, Any]:
    """Get detailed activity data from Strava API"""
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"include_all_efforts": False}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            return response.json()
    except Exception as e:
        logger.error(f"Error getting activity details: {e}")
        return {"error": str(e)}

async def get_activity_streams(
    access_token: str, 
    activity_id: str
) -> Dict[str, Any]:
    """Get activity streams (GPS data) from Strava API"""
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "keys": "latlng,altitude,time,distance",
        "key_by_type": True
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            return response.json()
    except Exception as e:
        logger.error(f"Error getting activity streams: {e}")
        return {"error": str(e)}

# GPX processing functions
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r

def load_gpx_points(gpx_content: str) -> List[Tuple[float, float]]:
    """Load points (latitude, longitude) from GPX content"""
    gpx = gpxpy.parse(gpx_content)
    points = []
    
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    
    return points

def simplify_points(points: List[Tuple[float, float]], tolerance: float = 0.0001) -> List[Tuple[float, float]]:
    """Simplify a list of points using Douglas-Peucker algorithm"""
    if len(points) < 3:
        return points
        
    line = LineString([(p[1], p[0]) for p in points])  # (lon, lat) for LineString
    simplified = line.simplify(tolerance)
    
    # Convert back to (lat, lon)
    return [(y, x) for x, y in simplified.coords]

def calculate_similarity(
    source_points: List[Tuple[float, float]],
    activity_points: List[Tuple[float, float]],
    max_deviation: float = 20.0  # Maximum deviation in meters
) -> Tuple[float, List[Tuple[float, float, float]]]:
    """Calculate similarity between source route and activity route"""
    # Create LineString from source points
    source_line = LineString([(p[1], p[0]) for p in source_points])  # (lon, lat) for LineString
    
    # Check each activity point against the source line
    deviations = []
    points_within_threshold = 0
    
    for lat, lon in activity_points:
        point = Point(lon, lat)  # (lon, lat) for Point
        distance = source_line.distance(point) * 111319.9  # Convert degrees to meters (approximate)
        deviations.append((lat, lon, distance))
        
        if distance <= max_deviation:
            points_within_threshold += 1
    
    # Calculate similarity score (percentage of points within threshold)
    similarity_score = points_within_threshold / len(activity_points) if activity_points else 0
    
    return similarity_score, deviations

def verify_activity_against_source(
    source_gpx_content: str,
    activity_points: List[Tuple[float, float]],
    activity_distance: float  # Distance in meters
) -> Dict[str, any]:
    """Verify if an activity matches a source GPX route"""
    # Check minimum distance requirement
    required_distance = settings.MIN_ACTIVITY_DISTANCE_KM * 1000  # Convert to meters
    if activity_distance < required_distance:
        return {
            "verified": False,
            "similarity_score": 0.0,
            "message": f"Activity distance ({activity_distance/1000:.1f}km) is less than required ({settings.MIN_ACTIVITY_DISTANCE_KM}km)"
        }
    
    # Load source route points
    try:
        source_points = load_gpx_points(source_gpx_content)
    except Exception as e:
        return {
            "verified": False,
            "similarity_score": 0.0,
            "message": f"Error loading source GPX: {str(e)}"
        }
    
    # Check if we have enough points
    if len(source_points) < 10 or len(activity_points) < 10:
        return {
            "verified": False,
            "similarity_score": 0.0,
            "message": "Not enough GPS points to perform verification"
        }
    
    # Simplify routes for faster comparison
    source_points = simplify_points(source_points)
    activity_points = simplify_points(activity_points)
    
    # Calculate similarity
    similarity_score, deviations = calculate_similarity(
        source_points,
        activity_points,
        max_deviation=settings.GPS_MAX_DEVIATION_METERS
    )
    
    # Check if similarity meets threshold
    verified = similarity_score >= settings.ROUTE_SIMILARITY_THRESHOLD
    
    return {
        "verified": verified,
        "similarity_score": similarity_score,
        "message": (
            f"Route verified successfully with {similarity_score:.1%} match"
            if verified else
            f"Route similarity ({similarity_score:.1%}) below required threshold ({settings.ROUTE_SIMILARITY_THRESHOLD:.1%})"
        )
    }

def convert_strava_streams_to_points(
    streams: Dict[str, any]
) -> List[Tuple[float, float]]:
    """Convert Strava API streams to list of points"""
    if not streams or "latlng" not in streams:
        return []
    
    latlng_data = streams["latlng"]["data"]
    return [(point[0], point[1]) for point in latlng_data if len(point) == 2]

async def load_source_gpx_file(filename: str) -> Tuple[bool, str]:
    """Load source GPX file content"""
    try:
        file_path = Path(settings.SOURCE_GPX_PATH) / filename
        
        if not file_path.exists():
            return False, f"File {filename} not found"
        
        with open(file_path, "r") as f:
            content = f.read()
        
        return True, content
    except Exception as e:
        return False, f"Error loading GPX file: {str(e)}"

async def update_leaderboard(db: Session, user_id: str) -> None:
    """Update leaderboard entry for user"""
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    
    # Count approved activities
    activity_count = db.query(Activity).filter(
        Activity.user_id == user_id
    ).count()
    
    # Update or create leaderboard entry
    leaderboard_entry = db.query(Leaderboard).filter(
        Leaderboard.id == user_id
    ).first()
    
    if leaderboard_entry:
        leaderboard_entry.activity_count = activity_count
        leaderboard_entry.last_updated = datetime.now()
    else:
        new_entry = Leaderboard(
            id=user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            activity_count=activity_count,
            last_updated=datetime.now()
        )
        db.add(new_entry)
    
    db.commit()