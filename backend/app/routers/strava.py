from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..core.config import settings
from ..services.email_service import send_strava_connected_email
from ..services.strava_service import (
    exchange_authorization_code, 
    get_strava_athlete_data
)

router = APIRouter()


@router.get("/strava/auth/{user_id}/{token}")
async def strava_auth(
    user_id: str,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle Strava OAuth callback with authorization code
    """
    # Check if we have the authorization code from Strava
    if not code:
        # No code provided, this is the initial request
        # Verify the token is valid
        verification = (
            db.query(models.VerificationToken)
            .filter(
                models.VerificationToken.user_id == user_id,
                models.VerificationToken.token == token,
                models.VerificationToken.type == "strava",
                models.VerificationToken.used == False,
                models.VerificationToken.expires_at > datetime.now()
            )
            .first()
        )
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired Strava authentication token",
            )
        
        # Get user
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Generate Strava authorization URL
        redirect_uri = f"{settings.FRONTEND_URL}/strava-auth/{user_id}/{token}?frontend_redirect=true"
        auth_url = (
            f"https://www.strava.com/oauth/authorize"
            f"?client_id={settings.STRAVA_CLIENT_ID}"
            f"&response_type=code"
            f"&redirect_uri={redirect_uri}"
            f"&approval_prompt=force"
            f"&scope=activity:read,profile:read_all"
        )
        
        return {"auth_url": auth_url}
    
    # We have the code, now exchange it for tokens
    # First verify the token again
    verification = (
        db.query(models.VerificationToken)
        .filter(
            models.VerificationToken.user_id == user_id,
            models.VerificationToken.token == token,
            models.VerificationToken.type == "strava",
            models.VerificationToken.used == False,
            models.VerificationToken.expires_at > datetime.now()
        )
        .first()
    )
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired Strava authentication token",
        )
    
    # Get user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Exchange authorization code for tokens
    redirect_uri = f"{settings.FRONTEND_URL}/strava-auth/{user_id}/{token}?frontend_redirect=true"
    token_response = await exchange_authorization_code(code, redirect_uri)
    
    if not token_response or "error" in token_response:
        error_msg = token_response.get("error", "Unknown error") if token_response else "Failed to get token"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to Strava: {error_msg}",
        )
    
    # Get athlete data
    athlete = token_response.get("athlete", {})
    
    # Save token to database
    existing_token = db.query(models.Token).filter(models.Token.user_id == user_id).first()
    
    if existing_token:
        # Update existing token
        existing_token.access_token = token_response["access_token"]
        existing_token.refresh_token = token_response["refresh_token"]
        existing_token.token_type = token_response["token_type"]
        existing_token.expires_at = token_response["expires_at"]
        existing_token.updated_at = datetime.now()
    else:
        # Create new token
        new_token = models.Token(
            user_id=user_id,
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type=token_response["token_type"],
            expires_at=token_response["expires_at"],
        )
        db.add(new_token)
    
    # Update user with Strava information
    user.strava_id = str(athlete.get("id", ""))
    user.strava_username = athlete.get("username", "")
    user.is_strava_connected = True
    
    # Mark verification token as used
    verification.used = True
    
    # Log the event
    audit_log = models.AuditLog(
        user_id=user_id,
        event_type="strava_connected",
        description=f"User {user.email} connected Strava account",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit_log)
    
    # Commit all changes
    db.commit()
    
    # Send confirmation email
    send_strava_connected_email(user.email, user.first_name)
    
    # Create initial leaderboard entry
    leaderboard_entry = db.query(models.Leaderboard).filter(models.Leaderboard.id == user_id).first()
    if not leaderboard_entry:
        new_entry = models.Leaderboard(
            id=user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            activity_count=0,
            last_updated=datetime.now()
        )
        db.add(new_entry)
        db.commit()
    
    return {
        "message": "Strava account successfully connected",
        "redirect_url": f"{settings.FRONTEND_URL}/thank-you"
    }


@router.post("/strava/webhook")
async def strava_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Handle Strava webhook events (not implemented in this version)
    """
    # This endpoint would handle Strava webhook events
    # For now, we'll use the background worker to check for new activities
    return {"message": "Webhook received"}


@router.get("/strava/webhook")
async def strava_webhook_verification(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify Strava webhook subscription (not implemented in this version)
    """
    # This would handle Strava webhook verification
    # For a hub.challenge response
    return {"message": "Webhook verification not implemented"}