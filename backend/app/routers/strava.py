# Modified version of backend/app/routers/strava.py
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import models
from ..database import get_db
from ..core.config import settings
from ..services.email_service import send_strava_connected_email
from ..services.strava_service import (
    exchange_authorization_code, 
    get_strava_athlete_data
)

# Configure debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("strava_auth")

router = APIRouter()


@router.get("/strava/auth/{user_id}/{token}")
async def strava_auth(
    user_id: str,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    code: Optional[str] = None,
    platform: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Handle Strava OAuth callback with authorization code
    
    The platform parameter can be used to detect mobile devices:
    - ios: iOS devices
    - android: Android devices
    - web: Desktop browsers (default)
    """
    # Add detailed logging
    logger.info(f"Strava auth called with user_id: {user_id}, token: {token[:5]}..., code: {code[:10] if code else 'None'}")
    logger.info(f"Query parameters: {dict(request.query_params)}")
    
    try:
        # Check if we have the authorization code from Strava
        
        # If code is provided, exchange it for tokens
        if code:
            # ... existing code for token exchange ...
            
            # Update user with Strava information
            try:
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
                
            except IntegrityError as e:
                # Rollback the transaction
                db.rollback()
                
                # Check if this is a duplicate Strava ID error
                error_text = str(e)
                if "ix_users_strava_id" in error_text and "duplicate key value" in error_text:
                    # Find which user has this Strava ID
                    strava_id = str(athlete.get("id", ""))
                    existing_user = db.query(models.User).filter(
                        models.User.strava_id == strava_id,
                        models.User.is_active == True
                    ).first()
                    
                    if existing_user:
                        user_email = existing_user.email
                        masked_email = mask_email(user_email)
                        
                        # Create a user-friendly error message
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"This Strava account is already connected to another user ({masked_email}). Please use a different Strava account or contact support if you believe this is an error."
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This Strava account is already connected to another user. Please use a different Strava account or contact support."
                        )
                else:
                    # Re-raise any other database errors with a user-friendly message
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="An error occurred while connecting your Strava account. Please try again later."
                    )

        if not code:
            # No code provided, this is the initial request
            # Verify the token is valid
            logger.debug("No code provided, verifying token")
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
                logger.warning(f"Invalid or expired Strava authentication token: {token[:5]}...")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid or expired Strava authentication token",
                )
            
            # Get user
            logger.debug(f"Getting user {user_id}")
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                logger.warning(f"User not found: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            
            logger.debug(f"Generating Strava auth URL for platform: {platform}")
            # Generate Strava authorization URL - use mobile endpoints if on mobile
            redirect_uri = f"{settings.FRONTEND_URL}/strava-auth/{user_id}/{token}?frontend_redirect=true"
            
            # Determine if we should use the mobile OAuth endpoint
            auth_base_url = "https://www.strava.com/oauth/authorize"
            if platform in ['ios', 'android']:
                auth_base_url = "https://www.strava.com/oauth/mobile/authorize"
            
            auth_url = (
                f"{auth_base_url}"
                f"?client_id={settings.STRAVA_CLIENT_ID}"
                f"&response_type=code"
                f"&redirect_uri={redirect_uri}"
                f"&approval_prompt=force"
                f"&scope=activity:read,profile:read_all"
            )
            
            logger.info(f"Returning auth URL: {auth_url[:60]}...")
            return {"auth_url": auth_url}
        
        # We have the code, now exchange it for tokens
        logger.info(f"Code provided, exchanging for tokens: {code[:10]}...")
        
        # First verify the token again
        logger.debug(f"Verifying token for code exchange: {token[:5]}...")
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
            logger.warning(f"Invalid or expired Strava authentication token: {token[:5]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired Strava authentication token",
            )
        
        # Get user
        logger.debug(f"Getting user {user_id}")
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Exchange authorization code for tokens
        logger.debug("Exchanging authorization code for tokens")
        redirect_uri = f"{settings.FRONTEND_URL}/strava-auth/{user_id}/{token}?frontend_redirect=true"
        token_response = await exchange_authorization_code(code, redirect_uri)
        
        # Log the token response (be careful not to log sensitive data in production)
        if token_response:
            logger.debug(f"Token response received with keys: {list(token_response.keys())}")
            if "errors" in token_response:
                logger.error(f"Strava API errors: {token_response['errors']}")
            if "error" in token_response:
                logger.error(f"Strava API error: {token_response['error']}")
        else:
            logger.error("No token response received from Strava")
        
        if not token_response or "error" in token_response or "errors" in token_response:
            error_msg = token_response.get("error", "Unknown error") if token_response else "Failed to get token"
            logger.error(f"Failed to connect to Strava: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Strava: {error_msg}",
            )
        
        # Get athlete data
        logger.debug("Getting athlete data from token response")
        athlete = token_response.get("athlete", {})
        
        # Save token to database
        logger.debug(f"Saving token to database for user: {user_id}")
        existing_token = db.query(models.Token).filter(models.Token.user_id == user_id).first()
        
        if existing_token:
            # Update existing token
            logger.debug("Updating existing token")
            existing_token.access_token = token_response["access_token"]
            existing_token.refresh_token = token_response["refresh_token"]
            existing_token.token_type = token_response["token_type"]
            existing_token.expires_at = token_response["expires_at"]
            existing_token.updated_at = datetime.now()
        else:
            # Create new token
            logger.debug("Creating new token")
            new_token = models.Token(
                user_id=user_id,
                access_token=token_response["access_token"],
                refresh_token=token_response["refresh_token"],
                token_type=token_response["token_type"],
                expires_at=token_response["expires_at"],
            )
            db.add(new_token)
        
        # Update user with Strava information
        logger.debug(f"Updating user with Strava information: ID {athlete.get('id', '')}")
        user.strava_id = str(athlete.get("id", ""))
        user.strava_username = athlete.get("username", "")
        user.is_strava_connected = True
        
        # Mark verification token as used
        logger.debug("Marking verification token as used")
        verification.used = True
        
        # Log the event
        logger.debug("Creating audit log entry")
        audit_log = models.AuditLog(
            user_id=user_id,
            event_type="strava_connected",
            description=f"User {user.email} connected Strava account",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(audit_log)
        
        # Commit all changes
        logger.debug("Committing database changes")
        db.commit()
        
        # Send confirmation email
        logger.debug(f"Sending confirmation email to {user.email}")
        send_strava_connected_email(user.email, user.first_name)
        
        # Create initial leaderboard entry
        logger.debug(f"Creating or updating leaderboard entry for user: {user_id}")
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
        
        logger.info("Strava connection successful")
        return {
            "message": "Strava account successfully connected",
            "redirect_url": f"{settings.FRONTEND_URL}/thank-you"
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        logger.error(f"HTTP Exception occurred: {traceback.format_exc()}")
        raise
    except Exception as e:
        # Log unexpected exceptions
        logger.error(f"Unexpected error in Strava auth: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Helper function to mask email addresses for privacy
def mask_email(email: str) -> str:
    """
    Mask an email address for privacy
    Example: john.doe@example.com -> j***e@e***e.com
    """
    if not email or '@' not in email:
        return "***"
        
    local, domain = email.split('@')
    
    # Mask the local part
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    
    # Mask the domain (before the dot)
    domain_parts = domain.split('.')
    if len(domain_parts[0]) <= 2:
        masked_domain = domain_parts[0][0] + "*"
    else:
        masked_domain = domain_parts[0][0] + "*" * (len(domain_parts[0]) - 2) + domain_parts[0][-1]
    
    # Combine everything
    return f"{masked_local}@{masked_domain}.{'.'.join(domain_parts[1:])}"

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
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify Strava webhook subscription
    """
    # Handle proper Strava webhook verification
    if hub_mode == "subscribe" and hub_verify_token == settings.STRAVA_WEBHOOK_VERIFY_TOKEN:
        return {"hub.challenge": hub_challenge}
    
    # Default response (not a proper verification request)
    return {"message": "Webhook verification endpoint"}