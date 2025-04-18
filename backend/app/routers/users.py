import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..core.config import settings
from ..services.email_service import send_email

router = APIRouter()


# Define Pydantic models for request and response validation
from pydantic import BaseModel, EmailStr, Field, validator


class UserRegistration(BaseModel):
    """Pydantic model for user registration"""
    first_name: str
    last_name: str
    age: int
    email: EmailStr
    terms_accepted: bool
    data_processing_accepted: bool

    @validator("age")
    def validate_age(cls, v):
        if v < 18:
            raise ValueError("You must be at least 18 years old to register")
        return v

    @validator("terms_accepted")
    def validate_terms(cls, v):
        if not v:
            raise ValueError("You must accept the terms and regulations")
        return v

    @validator("data_processing_accepted")
    def validate_data_processing(cls, v):
        if not v:
            raise ValueError("You must accept the data processing agreement")
        return v


class UserResponse(BaseModel):
    """Pydantic model for user response"""
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    is_email_verified: bool
    is_strava_connected: bool
    created_at: datetime

    class Config:
        orm_mode = True


class UnregisterRequest(BaseModel):
    """Pydantic model for unregister request"""
    email: EmailStr
    confirm: bool

    @validator("confirm")
    def validate_confirm(cls, v):
        if not v:
            raise ValueError("You must confirm that you want to delete your account")
        return v


@router.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserRegistration,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        else:
            # Reactivate user if previously unregistered
            existing_user.is_active = True
            existing_user.terms_accepted = user_data.terms_accepted
            existing_user.data_processing_accepted = user_data.data_processing_accepted
            existing_user.updated_at = datetime.now()
            db.commit()
            db.refresh(existing_user)
            
            # Create email verification token
            create_and_send_verification_token(existing_user, background_tasks, request, db)
            
            # Log event
            log_event(
                db, 
                existing_user.id, 
                "user_reactivated",
                f"User {existing_user.email} reactivated account",
                request
            )
            
            return existing_user
    
    # Create new user
    user = models.User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        age=user_data.age,
        email=user_data.email,
        terms_accepted=user_data.terms_accepted,
        data_processing_accepted=user_data.data_processing_accepted,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create and send verification token
    create_and_send_verification_token(user, background_tasks, request, db)
    
    # Log event
    log_event(
        db, 
        user.id, 
        "user_registered",
        f"User {user.email} registered",
        request
    )
    
    return user


@router.get("/users/verify/{user_id}/{token}")
def verify_email(
    user_id: uuid.UUID,
    token: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Verify user email with token
    """
    # Get verification token
    verification = (
        db.query(models.VerificationToken)
        .filter(
            models.VerificationToken.user_id == user_id,
            models.VerificationToken.token == token,
            models.VerificationToken.type == "email",
            models.VerificationToken.used == False,
            models.VerificationToken.expires_at > datetime.now()
        )
        .first()
    )
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired verification token",
        )
    
    # Get user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Mark user as verified
    user.is_email_verified = True
    
    # Mark token as used
    verification.used = True
    
    db.commit()
    
    # Log event
    log_event(
        db, 
        user.id, 
        "email_verified",
        f"User {user.email} verified email",
        request
    )
    
    # Create Strava authorization token
    strava_token = models.VerificationToken(
        user_id=user.id,
        token=secrets.token_urlsafe(32),
        type="strava",
        expires_at=datetime.now() + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS),
    )
    
    db.add(strava_token)
    db.commit()
    
    # Return success with Strava auth URL
    strava_auth_url = f"{settings.FRONTEND_URL}/strava-auth/{user.id}/{strava_token.token}"
    
    return {
        "message": "Email verified successfully",
        "strava_auth_url": strava_auth_url,
    }


@router.post("/users/unregister")
def request_unregister(
    unregister_data: UnregisterRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Request to unregister and delete user data
    """
    # Find user
    user = db.query(models.User).filter(
        models.User.email == unregister_data.email,
        models.User.is_active == True
    ).first()
    
    if not user:
        # Don't reveal if user exists or not for privacy
        return {
            "message": "If your email is registered, you will receive an unregister confirmation link"
        }
    
    # Create unregister token
    delete_token = models.VerificationToken(
        user_id=user.id,
        token=secrets.token_urlsafe(32),
        type="delete",
        expires_at=datetime.now() + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS),
    )
    
    db.add(delete_token)
    db.commit()
    
    # Build confirmation URL
    delete_url = f"{settings.FRONTEND_URL}/delete/{user.id}/{delete_token.token}"
    
    # Send email
    background_tasks.add_task(
        send_delete_confirmation_email,
        user.email,
        user.first_name,
        delete_url
    )
    
    # Log event
    log_event(
        db, 
        user.id, 
        "unregister_requested",
        f"User {user.email} requested account deletion",
        request
    )
    
    return {
        "message": "If your email is registered, you will receive an unregister confirmation link"
    }


@router.get("/users/delete/{user_id}/{token}")
def confirm_delete(
    user_id: uuid.UUID,
    token: str,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Confirm user deletion with token
    """
    # Get verification token
    verification = (
        db.query(models.VerificationToken)
        .filter(
            models.VerificationToken.user_id == user_id,
            models.VerificationToken.token == token,
            models.VerificationToken.type == "delete",
            models.VerificationToken.used == False,
            models.VerificationToken.expires_at > datetime.now()
        )
        .first()
    )
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired deletion token",
        )
    
    # Get user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Store email for confirmation
    user_email = user.email
    user_first_name = user.first_name
    
    # Mark user as inactive
    user.is_active = False
    user.is_email_verified = False
    user.is_strava_connected = False
    
    # Mark token as used
    verification.used = True
    
    # Remove from leaderboard
    leaderboard_entry = db.query(models.Leaderboard).filter(models.Leaderboard.id == user_id).first()
    if leaderboard_entry:
        db.delete(leaderboard_entry)
    
    # Log event
    log_event(
        db, 
        user.id, 
        "account_deleted",
        f"User {user_email} deleted account",
        request
    )
    
    db.commit()
    
    # Send confirmation email
    background_tasks.add_task(
        send_deletion_complete_email,
        user_email,
        user_first_name
    )
    
    return {
        "message": "Your account has been successfully deleted"
    }


@router.get("/users/leaderboard", response_model=List[Dict[str, Any]])
def get_leaderboard(
    limit: int = 20,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get leaderboard with top users
    """
    leaderboard = (
        db.query(models.Leaderboard)
        .order_by(models.Leaderboard.activity_count.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "first_name": entry.first_name,
            "last_name": entry.last_name,
            "activity_count": entry.activity_count,
        }
        for entry in leaderboard
    ]


# Helper functions
def create_and_send_verification_token(
    user: models.User,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session
) -> None:
    """Create and send email verification token"""
    # Generate verification token
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS)
    
    # Save token to database
    verification = models.VerificationToken(
        user_id=user.id,
        token=token,
        type="email",
        expires_at=expires,
    )
    
    db.add(verification)
    db.commit()
    
    # Build verification URL
    verify_url = f"{settings.FRONTEND_URL}/email-verify/{user.id}/{token}"
    
    # Send email verification
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.first_name,
        verify_url
    )


def log_event(
    db: Session,
    user_id: Optional[uuid.UUID],
    event_type: str,
    description: str,
    request: Request
) -> None:
    """Log system event"""
    audit_log = models.AuditLog(
        user_id=user_id,
        event_type=event_type,
        description=description,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    db.add(audit_log)
    db.commit()


# Email sending functions
def send_verification_email(email: str, first_name: str, verify_url: str) -> None:
    """Send email verification email"""
    subject = f"{settings.PROJECT_NAME} - Verify Your Email"
    content = f"""
    <html>
    <body>
        <h1>Hello {first_name},</h1>
        <p>Thank you for registering for the {settings.PROJECT_NAME}!</p>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verify_url}">Verify Email</a></p>
        <p>This link will expire in 48 hours.</p>
        <p>If you did not register for this event, please ignore this email.</p>
        <p>Best regards,<br>KMTB Team</p>
    </body>
    </html>
    """
    
    from ..services.email_service import send_email
    send_email(email, subject, content)


def send_delete_confirmation_email(email: str, first_name: str, delete_url: str) -> None:
    """Send confirmation email for account deletion"""
    subject = f"{settings.PROJECT_NAME} - Confirm Account Deletion"
    content = f"""
    <html>
    <body>
        <h1>Hello {first_name},</h1>
        <p>We received a request to delete your account from the {settings.PROJECT_NAME}.</p>
        <p>If you want to proceed with account deletion, please click the link below:</p>
        <p><a href="{delete_url}">Confirm Account Deletion</a></p>
        <p>This link will expire in 48 hours.</p>
        <p>If you did not request this, please ignore this email or contact us.</p>
        <p>Best regards,<br>KMTB Team</p>
    </body>
    </html>
    """
    
    from ..services.email_service import send_email
    send_email(email, subject, content)


def send_deletion_complete_email(email: str, first_name: str) -> None:
    """Send confirmation email that account deletion is complete"""
    subject = f"{settings.PROJECT_NAME} - Account Deleted"
    content = f"""
    <html>
    <body>
        <h1>Hello {first_name},</h1>
        <p>Your account and all associated data have been deleted from the {settings.PROJECT_NAME}.</p>
        <p>We're sorry to see you go, but you're welcome to join again in the future.</p>
        <p>Best regards,<br>KMTB Team</p>
    </body>
    </html>
    """
    
    from ..services.email_service import send_email
    send_email(email, subject, content)