import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
import pytz
import schedule
from sqlalchemy.orm import Session

from models import User, get_db
from settings import settings
from services import get_activities_after_date, ensure_fresh_token
from verification import verify_strava_activity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("worker.log")
    ]
)

logger = logging.getLogger("kmtb-worker")

async def process_user_activities(user_id: str, db: Session) -> None:
    """Process activities for a single user"""
    logger.info(f"Processing activities for user {user_id}")
    
    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True,
        User.is_email_verified == True,
        User.is_strava_connected == True
    ).first()
    
    if not user:
        logger.warning(f"User {user_id} not found or not eligible for processing")
        return
    
    # Ensure we have a fresh token
    token_success, token_value = await ensure_fresh_token(db, user_id)
    
    if not token_success:
        logger.error(f"Failed to get fresh token for user {user_id}: {token_value}")
        return
    
    # Determine timestamp to fetch activities after
    after_timestamp = int(time.time())
    
    if user.last_activity_check:
        # Use last check time minus 1 day (to ensure no activities are missed)
        check_time = user.last_activity_check.replace(tzinfo=pytz.UTC) - timedelta(days=1)
        after_timestamp = int(time.mktime(check_time.timetuple()))
    else:
        # If first check, get activities from the last 30 days
        check_time = datetime.now(pytz.UTC) - timedelta(days=30)
        after_timestamp = int(time.mktime(check_time.timetuple()))
    
    # Update last activity check time
    user.last_activity_check = datetime.now()
    db.commit()
    
    # Get recent activities
    activities = await get_activities_after_date(token_value, after_timestamp)
    
    if not activities:
        logger.info(f"No new activities found for user {user_id}")
        return
    
    logger.info(f"Found {len(activities)} new activities for user {user_id}")
    
    # Process each activity
    for activity in activities:
        activity_id = activity.get("id")
        
        # Verify activity
        logger.info(f"Verifying activity {activity_id} for user {user_id}")
        result = await verify_strava_activity(db, user_id, str(activity_id))
        
        if result.get("success", False) and result.get("verified", False):
            logger.info(f"Activity {activity_id} verified successfully")
        else:
            logger.info(f"Activity {activity_id} not verified: {result.get('message')}")

async def process_all_users(db: Session) -> None:
    """Process activities for all eligible users"""
    logger.info("Starting activity check for all users")
    
    # Get all eligible users
    users = db.query(User).filter(
        User.is_active == True,
        User.is_email_verified == True,
        User.is_strava_connected == True
    ).all()
    
    logger.info(f"Found {len(users)} eligible users")
    
    # Process each user
    for user in users:
        await process_user_activities(str(user.id), db)
    
    logger.info("Completed activity check for all users")

def job() -> None:
    """Main job function to be scheduled"""
    logger.info("Starting scheduled job")
    
    # Get DB session
    db = get_db()
    
    try:
        # Process all users
        asyncio.run(process_all_users(db))
    except Exception as e:
        logger.error(f"Error in scheduled job: {e}")
    
    logger.info("Finished scheduled job")

def check_run_time() -> bool:
    """
    Check if current time is within the allowed run times
    
    Returns:
        bool: True if current time is between 6:00 and 22:00, False otherwise
    """
    now = datetime.now(pytz.timezone(settings.TZ if hasattr(settings, 'TZ') else 'Europe/Warsaw'))
    return 6 <= now.hour < 22

def main() -> None:
    """Main function to schedule and run jobs"""
    logger.info("Starting worker service")
    
    # Schedule job every 2 hours
    schedule.every(2).hours.do(job)
    
    # Also run job immediately if within run times
    if check_run_time():
        job()
    
    # Run scheduler
    while True:
        # Only run jobs during specified hours
        if check_run_time():
            schedule.run_pending()
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()