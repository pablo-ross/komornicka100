import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from .. import models
from ..core.config import settings


async def exchange_authorization_code(
    code: str, 
    redirect_uri: str
) -> Dict[str, Any]:
    """
    Exchange Strava authorization code for access and refresh tokens
    
    Args:
        code: Authorization code from Strava
        redirect_uri: Redirect URI used in the authorization request
        
    Returns:
        Dict containing token response or error
    """
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": settings.STRAVA_CLIENT_ID,
        "client_secret": settings.STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            return response.json()
    except Exception as e:
        print(f"Error exchanging authorization code: {e}")
        return {"error": str(e)}


async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh Strava access token using refresh token
    
    Args:
        refresh_token: Refresh token from Strava
        
    Returns:
        Dict containing new token response or error
    """
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
        print(f"Error refreshing access token: {e}")
        return {"error": str(e)}


async def get_strava_athlete_data(access_token: str) -> Dict[str, Any]:
    """
    Get athlete data from Strava API
    
    Args:
        access_token: Valid Strava access token
        
    Returns:
        Dict containing athlete data or error
    """
    url = "https://www.strava.com/api/v3/athlete"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.json()
    except Exception as e:
        print(f"Error getting athlete data: {e}")
        return {"error": str(e)}


async def get_activities_after_date(
    access_token: str, 
    after_timestamp: int,
    activity_type: str = "Ride",
    page: int = 1,
    per_page: int = 30
) -> List[Dict[str, Any]]:
    """
    Get activities from Strava API after a specific date
    
    Args:
        access_token: Valid Strava access token
        after_timestamp: Unix timestamp to filter activities after
        activity_type: Type of activities to filter (default: Ride)
        page: Page number for pagination
        per_page: Number of items per page
        
    Returns:
        List of activities or empty list on error
    """
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
        print(f"Error getting activities: {e}")
        return []


async def get_activity_by_id(
    access_token: str, 
    activity_id: str
) -> Dict[str, Any]:
    """
    Get detailed activity data from Strava API
    
    Args:
        access_token: Valid Strava access token
        activity_id: Strava activity ID
        
    Returns:
        Dict containing activity data or error
    """
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"include_all_efforts": False}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            return response.json()
    except Exception as e:
        print(f"Error getting activity details: {e}")
        return {"error": str(e)}


async def get_activity_streams(
    access_token: str, 
    activity_id: str
) -> Dict[str, Any]:
    """
    Get activity streams (GPS data) from Strava API
    
    Args:
        access_token: Valid Strava access token
        activity_id: Strava activity ID
        
    Returns:
        Dict containing activity streams or error
    """
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
        print(f"Error getting activity streams: {e}")
        return {"error": str(e)}


async def create_strava_auth_url(
    user_id: str,
    token: str,
    platform: Optional[str] = None
) -> str:
    """
    Create Strava authentication URL based on platform
    
    Args:
        user_id: User ID for the redirect
        token: Verification token for the redirect
        platform: Platform (ios, android, web)
        
    Returns:
        Strava authentication URL
    """
    # Generate redirect URI (same for all platforms)
    redirect_uri = f"{settings.FRONTEND_URL}/strava-auth/{user_id}/{token}?frontend_redirect=true"
    
    # Determine base URL based on platform
    oauth_base_url = "https://www.strava.com/oauth/authorize"
    if platform in ['ios', 'android']:
        oauth_base_url = "https://www.strava.com/oauth/mobile/authorize"
    
    # Create the full auth URL
    auth_url = (
        f"{oauth_base_url}"
        f"?client_id={settings.STRAVA_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&approval_prompt=force"
        f"&scope=activity:read,profile:read_all"
    )
    
    return auth_url


async def ensure_fresh_token(db: Session, user_id: str) -> Tuple[bool, str]:
    """
    Ensure the user has a fresh Strava access token
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Tuple of (success, access_token)
    """
    # Get token from database
    token = db.query(models.Token).filter(models.Token.user_id == user_id).first()
    
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