import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    String, Text, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """User model for contest participants"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    
    # Strava information
    strava_id = Column(String, unique=True, index=True, nullable=True)
    strava_username = Column(String, nullable=True)
    
    # Status flags
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    is_strava_connected = Column(Boolean, default=False)
    terms_accepted = Column(Boolean, default=False)
    data_processing_accepted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_activity_check = Column(DateTime, nullable=True)
    
    # Relationships
    activities = relationship("Activity", back_populates="user")
    activity_attempts = relationship("ActivityAttempt", back_populates="user")
    tokens = relationship("Token", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User {self.email}>"


class Activity(Base):
    """Verified and approved user activities"""
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    
    # Relationships
    user = relationship("User", back_populates="activities")
    source_gpx = relationship("SourceGPX", back_populates="activities")
    
    def __repr__(self):
        return f"<Activity {self.name} - {self.start_date}>"


class ActivityAttempt(Base):
    """All activities checked (for analytics)"""
    __tablename__ = "activity_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    
    # Relationships
    user = relationship("User", back_populates="activity_attempts")
    source_gpx = relationship("SourceGPX", back_populates="activity_attempts")
    
    def __repr__(self):
        return f"<ActivityAttempt {self.name} - {self.start_date} - {'Verified' if self.is_verified else 'Failed'}>"


class Token(Base):
    """OAuth tokens for Strava API access"""
    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Strava OAuth tokens
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    token_type = Column(String, nullable=False)
    expires_at = Column(Integer, nullable=False)  # Unix timestamp
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    
    def __repr__(self):
        return f"<Token for user_id {self.user_id}>"


class SourceGPX(Base):
    """Predefined routes that users need to match"""
    __tablename__ = "source_gpxs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String, nullable=False)
    distance = Column(Float, nullable=False)  # in meters
    
    # Status flags
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    activities = relationship("Activity", back_populates="source_gpx")
    activity_attempts = relationship("ActivityAttempt", back_populates="source_gpx")
    
    def __repr__(self):
        return f"<SourceGPX {self.name}>"


class VerificationToken(Base):
    """One-time tokens for email verification and Strava auth"""
    __tablename__ = "verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=False)  # 'email', 'strava', 'delete'
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<VerificationToken {self.type} for user_id {self.user_id}>"


class AuditLog(Base):
    """System events log"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String, nullable=False)  # 'registration', 'verification', 'strava_auth', etc.
    description = Column(Text, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog {self.event_type} at {self.created_at}>"


class Leaderboard(Base):
    """Materialized view for leaderboard (updated by worker)"""
    __tablename__ = "leaderboard"

    id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    activity_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Leaderboard {self.first_name} {self.last_name} - {self.activity_count} activities>"