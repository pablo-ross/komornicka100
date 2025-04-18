import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings loaded from environment variables"""
    
    # Project settings
    PROJECT_NAME = os.getenv("PROJECT_NAME", "Komornicka 100")
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    
    # Strava API settings
    STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
    STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
    
    # Email settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    
    # URL settings
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # GPX verification settings
    SOURCE_GPX_PATH = os.getenv("SOURCE_GPX_PATH", "data")
    ROUTE_SIMILARITY_THRESHOLD = float(os.getenv("ROUTE_SIMILARITY_THRESHOLD", "0.8"))
    GPS_MAX_DEVIATION_METERS = float(os.getenv("GPS_MAX_DEVIATION_METERS", "20.0"))
    MIN_ACTIVITY_DISTANCE_KM = float(os.getenv("MIN_ACTIVITY_DISTANCE_KM", "100.0"))

# Create global settings object
settings = Settings()