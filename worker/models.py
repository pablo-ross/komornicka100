from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from settings import settings

# Create database engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

class User(Base):
    """User model for contest participants"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    
    # Strava information
    strava_id = Column(String, unique=True, index=True, nullable=True)
    
    # Status flags
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    is_strava_connected = Column(Boolean, default=False)
    
    # Timestamps
    last_activity_check = Column(DateTime, nullable=True)

class Activity(Base):
    """Verified and approved user activities"""
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strava_activity_id = Column(String, unique=True, index=True, nullable=False)
    source_gpx_id = Column(UUID(as_uuid=True), ForeignKey("source_gpxs.id"), nullable=False)
    
    # Activity details
    name = Column(String, nullable=False)
    distance = Column(Float, nullable=False)  # in meters
    duration = Column(Integer, nullable=False)  # in seconds
    start_date = Column(DateTime, nullable=False)
    
    # Verification details
    verified_at = Column(DateTime, default=func.now())
    similarity_score = Column(Float, nullable=False)  # how closely the activity matches the source GPX

class ActivityAttempt(Base):
    """All activities checked (for analytics)"""
    __tablename__ = "activity_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strava_activity_id = Column(String, index=True, nullable=False)
    source_gpx_id = Column(UUID(as_uuid=True), ForeignKey("source_gpxs.id"), nullable=True)
    
    # Activity details
    name = Column(String, nullable=False)
    distance = Column(Float, nullable=False)  # in meters
    duration = Column(Integer, nullable=False)  # in seconds
    start_date = Column(DateTime, nullable=False)
    
    # Verification details
    checked_at = Column(DateTime, default=func.now())
    is_verified = Column(Boolean, default=False)
    similarity_score = Column(Float, nullable=True)
    verification_message = Column(String, nullable=True)  # reason for failure or success

class Token(Base):
    """OAuth tokens for Strava API access"""
    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Strava OAuth tokens
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    token_type = Column(String, nullable=False)
    expires_at = Column(Integer, nullable=False)  # Unix timestamp
    
    # Timestamps
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SourceGPX(Base):
    """Predefined routes that users need to match"""
    __tablename__ = "source_gpxs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String, nullable=False)
    distance = Column(Float, nullable=False)  # in meters
    
    # Status flags
    is_active = Column(Boolean, default=True)

class Leaderboard(Base):
    """Materialized view for leaderboard (updated by worker)"""
    __tablename__ = "leaderboard"

    id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    activity_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now())

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()